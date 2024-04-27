# Task Management

# Step to run the project
1. `docker compose up`. To up and running the `postgres`.
2. `alembic upgrade head`. To apply migration files.
3. `uvicorn main:app --reload`. To run the project.

# Postman collection
TODO

# ListView
`filter` and `pagination`

# Undo Mechanism
post = make new instance with new `identifier` 
put = make new instance with new `identifier`, but reuse the old `id`.
delete = mark as deleted.
post `/undo/<identifier>` = undelete the instance
TODO

# pylintrc
TODO

# Test
Rather than using POSTMAN click. I prefer run the script.
It mutates the database. Then be careful.

You need to add `User` first start with `id=1`.
