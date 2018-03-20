all:prepare_test_env test destroy_test_env

prepare_test_env:
	docker run --name test_mysql --rm -d -p 3306:3306 -e MYSQL_ALLOW_EMPTY_PASSWORD=yes mysql
	docker run --name test_postgres --rm -d -p 5432:5432 -e POSTGRES_PASSWORD="" postgres
	sleep 10 # waiting for services ready
	docker exec -ti test_mysql mysql -u root -e 'create database peeweext;'
	docker exec -ti test_postgres psql -c 'create database peeweext;' -U postgres

destroy_test_env:
	docker stop test_mysql test_postgres

test:
	pytest tests
