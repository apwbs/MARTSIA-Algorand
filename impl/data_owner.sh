echo "Data owner start"
python3 data_owner.py -g
echo "Data owner key generation done"
python3 data_owner.py -c
echo "Data owner ciphering done"