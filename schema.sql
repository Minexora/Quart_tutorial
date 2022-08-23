drop table if exists todos;
create table todos (
    id integer  PRIMARY KEY autoincrement,
    complate boolean not null default false,
    due timestamptz,
    task text not null
);