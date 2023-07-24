# Read public key of manufacter and suppliers
set -e
python3 reader_public_key.py --reader 'DATAOWNER_MANUFACTURER'
echo "✅ Readed public key of MANUFACTURER"
python3 reader_public_key.py --reader 'READER_SUPPLIER1'
echo "✅ Readed public key of SUPPLIER1"
python3 reader_public_key.py --reader 'READER_SUPPLIER2'
echo "✅ Readed public key of SUPPLIER2"

python3 attribute_certifier.py 
echo "✅ Attribute certifier done"