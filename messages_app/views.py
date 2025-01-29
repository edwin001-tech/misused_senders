import csv
import os
from django.http import JsonResponse
from django.db import connection, OperationalError
from django.core.mail import EmailMessage
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

# Alternative Classifier (valhalla/distilbart-mnli-12-9)
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def classify_messages_batch(messages):
    candidate_labels = ["Transactional", "Promotional"]
    hypothesis_template = "This message is {}."
    try:
        results = classifier(messages, candidate_labels, hypothesis_template=hypothesis_template)
        return [result['labels'][0] for result in results]
    except Exception as e:
        logger.error(f"Error in batch classification: {str(e)}")
        return ["Unknown"] * len(messages)


def fetch_records_streaming(cursor, query, batch_size):
    cursor.execute(query)
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        yield rows


def write_to_csv(data, file_path):
    """
    Writes the misused sender IDs to a CSV file.
    """
    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["Date","sender_id", "message", "classifiedType", "expectedType"])
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        logger.error(f"Failed to write CSV: {str(e)}")
        raise


def send_email_with_attachment(subject, message, recipient_email, csv_file_path):
    """
    Sends an email with the specified CSV file as an attachment.
    """
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            to=[recipient_email]
        )
        email.attach_file(csv_file_path)
        email.send()
        logger.info("Email sent successfully with the CSV attachment.")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


def find_misused_sender_ids(request):
    BATCH_SIZE = 1000  # Batch size for streaming
    misused_senders = []
    offset = 0

    query = """
    SELECT DISTINCT onfon.sms_campaigns.message,
                    onfon.sms_campaigns.sender_id,
                    onfon.sms_sender_ids.sender_id_type,
                    onfon.sms_campaigns.created_at
    FROM onfon.sms_campaigns
    INNER JOIN onfon.sms_sender_ids
        ON onfon.sms_campaigns.client_id = onfon.sms_sender_ids.client_id
    WHERE onfon.sms_campaigns.created_at >= NOW() - INTERVAL 1 DAY
      AND onfon.sms_sender_ids.sender_id_type = 'Transactional';
    """

    # Define the CSV file path
    csv_file_path = os.path.join(os.path.dirname(__file__), "misused_senders.csv")

    try:
        with connection.cursor() as cursor:
            for batch in fetch_records_streaming(cursor, query, BATCH_SIZE):
                messages = [row[0] for row in batch]
                classifications = classify_messages_batch(messages)

                for (message, source, sender_id_type, created_at), classified_type in zip(batch, classifications):
                    if classified_type != sender_id_type:
                        misused_senders.append({
                            'Date': created_at,
                            'sender_id': source,
                            'message': message,
                            'classifiedType': classified_type,
                            'expectedType': sender_id_type,
                        })

                logger.info(f"Processed {offset + len(batch)} records so far...")
                offset += BATCH_SIZE

        # Write to CSV file
        write_to_csv(misused_senders, csv_file_path)

        # Send email with the attachment
        send_email_with_attachment(
            subject="Misused Sender IDs Report",
            message="Please find the attached report of misused sender IDs.",
            recipient_email="esalikho@onfonmedia.com",
            csv_file_path=csv_file_path
        )

    except OperationalError as e:
        logger.error(f"Database operation failed: {str(e)}")
        return JsonResponse({'error': 'Database connection issue. Check server logs.'}, status=500)
    except Exception as e:
        logger.error(f"Error processing records: {str(e)}")
        return JsonResponse({'error': 'Failed to process records. Check server logs.'}, status=500)
    finally:
        # Clean up the file after sending the email
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

    return JsonResponse({'message': 'Misused sender IDs have been processed and emailed successfully.'})
