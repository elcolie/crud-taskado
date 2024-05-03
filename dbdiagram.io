Table TaskContent{
  identifier varchar
  id int
  title varchar
  description varchar
  due_date date
  status enum
  is_deleted bool
  created_by int
  create_at datetime
}

Table CurrentTaskContent{
  identifer varchar
  id int
  created_by int
  updated_by int
  created_at datetine
  updated_at datetime
}

Table User{
  id int
  username varchar
}
Ref: TaskContent.created_by > User.id
Ref: CurrentTaskContent.created_by > User.id
Ref: CurrentTaskContent.updated_by > User.id
