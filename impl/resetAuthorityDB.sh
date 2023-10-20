# Go to the directory where the databases are stored
cd files

# Delete and recreate the databases authority1
cd ../authority1
rm -f authority1.db
sqlite3 authority1.db < ../commands.sql
echo "authority1.db resetted (4/7)"

# Delete and recreate the databases authority2
cd ../authority2
rm -f authority2.db
sqlite3 authority2.db < ../commands.sql
echo "authority2.db resetted (5/7)"

# Delete and recreate the databases authority3
cd ../authority3
rm -f authority3.db
sqlite3 authority3.db < ../commands.sql
echo "authority3.db resetted (6/7)"

# Delete and recreate the databases authority4
cd ../authority4
rm -f authority4.db
sqlite3 authority4.db < ../commands.sql
echo "authority4.db resetted (7/7)"