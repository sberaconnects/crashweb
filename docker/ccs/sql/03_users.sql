USE coredumps;

create user 'ccs'@'%';
grant all privileges on coredumps.* to 'ccs'@'%';
create user 'apache'@'%';
grant select on coredumps.* to 'apache'@'%';
grant insert, update, delete on coredumps.cla_ticket to 'apache'@'%';

flush privileges;

