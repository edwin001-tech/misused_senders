#!/bin/bash

# Add the cron job
#echo "* * * * * /usr/local/bin/python /app/run_daily.py >> /app/daily_task.log 2>&1" > /etc/cron.d/my-cron
chmod +x /app/run_daily.py
#chmod 0644 /etc/cron.d/my-cron
#crontab /etc/cron.d/my-cron

# Start the cron service
cron

#logs
tail -f /var/log/cron.log /app/daily_task.log
