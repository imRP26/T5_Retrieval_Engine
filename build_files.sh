
echo " BUILD STARTED"
python3.10 -m pip install -r requirements.txt
python3.10 manage.py collectstatic --noinput --clear
echo " BUILD FINISHED"