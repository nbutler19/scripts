#!/bin/bash

date=$(date +%Y%m%d)
backup_file=
fix_sql_file=
scrubbed_backup_file=

mysqlhost=
mysqldb=
mysqluser=
mysqlpass=
s3path=
s3pickup=

s3cmd get --force s3:///${s3_path}/${backup_file}.bz2 /tmp/${backup_file}.bz2

bunzip2 /tmp/${backup_file}.bz2

# Change charset to utf8
sed -i 's/latin1/utf8/g' /tmp/${backup_file}

# Get rid of stored procs (can't use them on rds)
sed -i '/DELIMITER\ ;;/{
N
N
N
N
N
N
N
N
N
N
N
N
N
N
N
N
N
N
/DELIMITER\ ;/d}' /tmp/${backup_file}

# Keep script self contained
# Change these values to the actual table name and column name
cat >${fix_sql_file} <<EOF
update tbl_name set col_name = replace(col_name, 'â€™', '\'');
update tbl_name set col_name = replace(col_name, 'â€¦','...');
update tbl_name set col_name = replace(col_name, 'â€“','-');
update tbl_name set col_name = replace(col_name, 'â€œ','"');
update tbl_name set col_name = replace(col_name, 'â€','"');
update tbl_name set col_name = replace(col_name, 'â€˜','\'');
update tbl_name set col_name = replace(col_name, 'â€¢','-');
update tbl_name set col_name = replace(col_name, 'â€¡','c');
update tbl_name set col_name = replace(col_name, 'â€”','"');
update tbl_name set col_name = replace(col_name, 'â€¨','');
update tbl_name set col_name = replace(col_name, 'â€©','©');
update tbl_name set col_name = replace(col_name, 'â€³','"');
update tbl_name set col_name = replace(col_name, 'â€¬â€ª','');
update tbl_name set col_name = replace(col_name, 'Ã©â€š','é');
update tbl_name set col_name = replace(col_name, 'Â','');
update tbl_name set col_name = replace(col_name, 'â€','-');
update tbl_name set col_name = replace(col_name, 'â€','-');
update tbl_name set col_name = replace(col_name, 'â€','-');
update tbl_name set col_name = replace(col_name, 'Ã©','é');
update tbl_name set col_name = replace(col_name, 'Ã€','À');
update tbl_name set col_name = replace(col_name, 'Ã¤','ä');
update tbl_name set col_name = replace(col_name, 'â˜†','☆'); 
update tbl_name set col_name = replace(col_name, 'Ã ','à'); 
EOF

mysql --default-character-set=utf8 -h $mysqlhost -u $mysqluser -p$mysqlpass $mysqldb < /tmp/${backup_file}
mysql --default-character-set=utf8 -h $mysqlhost -u $mysqluser -p$mysqlpass $mysqldb < ${fix_sql_file}

rm -f /tmp/${backup_file}
rm -f ${fix_sql_file}

mysqldump --default-character-set=utf8 -h $mysqlhost -u $mysqluser -p$mysqlpass $mysqldb | bzip2 > /tmp/${scrubbed_backup_file}
s3cmd put /tmp/${scrubbed_backup_file}.bz2 s3://${s3_pickup}/

rm -f /tmp/${scrubbed_backup_file}.bz2
