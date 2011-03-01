#!/bin/bash -x

date=$(date +%Y%m%d)
backup_file=${date}-iac_live_innodb.sql
fix_sql_file=/tmp/tdb_fix.sql
s3_path=

mysqlhost=
mysqldb=
mysqluser=
mysqlpass=

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
cat >${fix_sql_file} <<EOF
update assets set name = replace(name, 'â€™', '\'');
update assets set name = replace(name, 'â€¦','...');
update assets set name = replace(name, 'â€“','-');
update assets set name = replace(name, 'â€œ','"');
update assets set name = replace(name, 'â€','"');
update assets set name = replace(name, 'â€˜','\'');
update assets set name = replace(name, 'â€¢','-');
update assets set name = replace(name, 'â€¡','c');
update cheats set badge_name = replace(badge_name, 'â€™', '\'');
update cheats set badge_name = replace(badge_name, 'â€¦','...');
update cheats set badge_name = replace(badge_name, 'â€“','-');
update cheats set badge_name = replace(badge_name, 'â€œ','"');
update cheats set badge_name = replace(badge_name, 'â€','"');
update cheats set badge_name = replace(badge_name, 'â€˜','\'');
update cheats set badge_name = replace(badge_name, 'â€¢','-');
update cheats set badge_name = replace(badge_name, 'â€¡','c');
update cheats set deck = replace(deck, 'â€™', '\'');
update cheats set deck = replace(deck, 'â€¦','...');
update cheats set deck = replace(deck, 'â€“','-');
update cheats set deck = replace(deck, 'â€œ','"');
update cheats set deck = replace(deck, 'â€','"');
update cheats set deck = replace(deck, 'â€˜','\'');
update cheats set deck = replace(deck, 'â€¢','-');
update cheats set deck = replace(deck, 'â€¡','c');
update cheats set external_link_title = replace(external_link_title, 'â€™', '\'');
update cheats set external_link_title = replace(external_link_title, 'â€¦','...');
update cheats set external_link_title = replace(external_link_title, 'â€“','-');
update cheats set external_link_title = replace(external_link_title, 'â€œ','"');
update cheats set external_link_title = replace(external_link_title, 'â€','"');
update cheats set external_link_title = replace(external_link_title, 'â€˜','\'');
update cheats set external_link_title = replace(external_link_title, 'â€¢','-');
update cheats set external_link_title = replace(external_link_title, 'â€¡','c');
update cheats set name = replace(name, 'â€™', '\'');
update cheats set name = replace(name, 'â€¦','...');
update cheats set name = replace(name, 'â€“','-');
update cheats set name = replace(name, 'â€œ','"');
update cheats set name = replace(name, 'â€','"');
update cheats set name = replace(name, 'â€˜','\'');
update cheats set name = replace(name, 'â€¢','-');
update cheats set name = replace(name, 'â€¡','c');
update cheats set page_title = replace(page_title, 'â€™', '\'');
update cheats set page_title = replace(page_title, 'â€¦','...');
update cheats set page_title = replace(page_title, 'â€“','-');
update cheats set page_title = replace(page_title, 'â€œ','"');
update cheats set page_title = replace(page_title, 'â€','"');
update cheats set page_title = replace(page_title, 'â€˜','\'');
update cheats set page_title = replace(page_title, 'â€¢','-');
update cheats set page_title = replace(page_title, 'â€¡','c');
update cheats set subheadline = replace(subheadline, 'â€™', '\'');
update cheats set subheadline = replace(subheadline, 'â€¦','...');
update cheats set subheadline = replace(subheadline, 'â€“','-');
update cheats set subheadline = replace(subheadline, 'â€œ','"');
update cheats set subheadline = replace(subheadline, 'â€','"');
update cheats set subheadline = replace(subheadline, 'â€˜','\'');
update cheats set subheadline = replace(subheadline, 'â€¢','-');
update cheats set subheadline = replace(subheadline, 'â€¡','c');
update galleries set name = replace(name, 'â€™', '\'');
update galleries set name = replace(name, 'â€¦','...');
update galleries set name = replace(name, 'â€“','-');
update galleries set name = replace(name, 'â€œ','"');
update galleries set name = replace(name, 'â€','"');
update galleries set name = replace(name, 'â€˜','\'');
update galleries set name = replace(name, 'â€¢','-');
update galleries set name = replace(name, 'â€¡','c');
update galleries_to_items set caption = replace(caption, 'â€™', '\'');
update galleries_to_items set caption = replace(caption, 'â€¦','...');
update galleries_to_items set caption = replace(caption, 'â€“','-');
update galleries_to_items set caption = replace(caption, 'â€œ','"');
update galleries_to_items set caption = replace(caption, 'â€','"');
update galleries_to_items set caption = replace(caption, 'â€˜','\'');
update galleries_to_items set caption = replace(caption, 'â€¢','-');
update galleries_to_items set caption = replace(caption, 'â€¡','c');
update galleries_to_items set credit = replace(credit, 'â€™', '\'');
update galleries_to_items set credit = replace(credit, 'â€¦','...');
update galleries_to_items set credit = replace(credit, 'â€“','-');
update galleries_to_items set credit = replace(credit, 'â€œ','"');
update galleries_to_items set credit = replace(credit, 'â€','"');
update galleries_to_items set credit = replace(credit, 'â€˜','\'');
update galleries_to_items set credit = replace(credit, 'â€¢','-');
update galleries_to_items set credit = replace(credit, 'â€¡','c');
update galleries_to_items set title = replace(title, 'â€™', '\'');
update galleries_to_items set title = replace(title, 'â€¦','...');
update galleries_to_items set title = replace(title, 'â€“','-');
update galleries_to_items set title = replace(title, 'â€œ','"');
update galleries_to_items set title = replace(title, 'â€','"');
update galleries_to_items set title = replace(title, 'â€˜','\'');
update galleries_to_items set title = replace(title, 'â€¢','-');
update galleries_to_items set title = replace(title, 'â€¡','c');
update posts set bodytext = replace(bodytext, 'â€™', '\'');
update posts set bodytext = replace(bodytext, 'â€¦','...');
update posts set bodytext = replace(bodytext, 'â€“','-');
update posts set bodytext = replace(bodytext, 'â€œ','"');
update posts set bodytext = replace(bodytext, 'â€','"');
update posts set bodytext = replace(bodytext, 'â€˜','\'');
update posts set bodytext = replace(bodytext, 'â€¢','-');
update posts set bodytext = replace(bodytext, 'â€¡','c');
update posts set page_title = replace(page_title, 'â€™', '\'');
update posts set page_title = replace(page_title, 'â€¦','...');
update posts set page_title = replace(page_title, 'â€“','-');
update posts set page_title = replace(page_title, 'â€œ','"');
update posts set page_title = replace(page_title, 'â€','"');
update posts set page_title = replace(page_title, 'â€˜','\'');
update posts set page_title = replace(page_title, 'â€¢','-');
update posts set page_title = replace(page_title, 'â€¡','c');
update posts set second_featured_title = replace(second_featured_title, 'â€™', '\'');
update posts set second_featured_title = replace(second_featured_title, 'â€¦','...');
update posts set second_featured_title = replace(second_featured_title, 'â€“','-');
update posts set second_featured_title = replace(second_featured_title, 'â€œ','"');
update posts set second_featured_title = replace(second_featured_title, 'â€','"');
update posts set second_featured_title = replace(second_featured_title, 'â€˜','\'');
update posts set second_featured_title = replace(second_featured_title, 'â€¢','-');
update posts set second_featured_title = replace(second_featured_title, 'â€¡','c');
update posts set top_featured_title = replace(top_featured_title, 'â€™', '\'');
update posts set top_featured_title = replace(top_featured_title, 'â€¦','...');
update posts set top_featured_title = replace(top_featured_title, 'â€“','-');
update posts set top_featured_title = replace(top_featured_title, 'â€œ','"');
update posts set top_featured_title = replace(top_featured_title, 'â€','"');
update posts set top_featured_title = replace(top_featured_title, 'â€˜','\'');
update posts set top_featured_title = replace(top_featured_title, 'â€¢','-');
update posts set top_featured_title = replace(top_featured_title, 'â€¡','c');
update users set last_name = replace(last_name, 'â€™', '\'');
update users set last_name = replace(last_name, 'â€¦','...');
update users set last_name = replace(last_name, 'â€“','-');
update users set last_name = replace(last_name, 'â€œ','"');
update users set last_name = replace(last_name, 'â€','"');
update users set last_name = replace(last_name, 'â€˜','\'');
update users set last_name = replace(last_name, 'â€¢','-');
update users set last_name = replace(last_name, 'â€¡','c');
update users set first_name = replace(first_name, 'â€™', '\'');
update users set first_name = replace(first_name, 'â€¦','...');
update users set first_name = replace(first_name, 'â€“','-');
update users set first_name = replace(first_name, 'â€œ','"');
update users set first_name = replace(first_name, 'â€','"');
update users set first_name = replace(first_name, 'â€˜','\'');
update users set first_name = replace(first_name, 'â€¢','-');
update users set first_name = replace(first_name, 'â€¡','c');
alter table assets add unique assets_index (id);
alter table galleries_to_items add index galleries_to_items_items_index (items_id);
alter table galleries_to_items add index galleries_to_items_galleries_index (galleries_id);
alter table galleries add unique galleries_index (id);
alter table users add index user_asserts_index (assets_id);
EOF

mysql --default-character-set=utf8 -h $mysqlhost -u $mysqluser -p$mysqlpass $mysqldb < /tmp/${backup_file}
mysql --default-character-set=utf8 -h $mysqlhost -u $mysqluser -p$mysqlpass $mysqldb < ${fix_sql_file}

rm -f /tmp/${backup_file}
rm -f ${fix_sql_file}
