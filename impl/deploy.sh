set -e
cd blockchain

cd AttributeCertifierContract
echo "Deploying AttributeCertifierContract"
python3.10 AttributeCertifierContractMainCreation.py -d
#python3.10 blockchain/AttributeCertifierContract/AttributeCertifierContractMain.py -d
echo "Deployed AttributeCertifierContract \n"

cd ../MessageContract
echo "Deploying MessageContract"
python3.10 MessageContractMainCreation.py -d
#python3.10 blockchain/MessageContract/MessageContractMain.py -d
echo "Deployed MessageContract \n"

cd ../BoxContract
echo "Deploying BoxContract"
python3.10 BoxContractMainCreation.py -d
#python3.10 blockchain/PublicKeySKM/BoxContractMainCreation.py -d
echo "Deployed BoxContract \n"

cd ../PublicKeysReadersContract
echo "Deploying PKReadersContract"
python3.10 PKReadersContractMainCreation.py -d
#python3.10 blockchain/PublicKeysReadersContract/PKReadersContractMain.py -d
echo "Deployed PKReadersContract"