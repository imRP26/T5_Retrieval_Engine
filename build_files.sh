
echo " BUILD STARTED"
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
echo " BUILD FINISHED"