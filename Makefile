PSWD=foobar
#IMAGE=timescale/timescaledb
IMAGE=timescale/timescaledb-postgis

images:
	docker build -f docker/Dockerfile.hdfs -t tdm/hdfs docker
	#docker build -f docker/Dockerfile.tiledb -t tdm/tiledb docker
	docker build -f docker/Dockerfile.tiledb.new -t tdm/tiledb docker

docker/docker_compose.yml: docker/docker-compose.yml-tmpl
	sed -e "s^LOCAL_PATH^$${PWD}^"   \
	    -e "s^USER_UID^$$(id -u)^" \
	    -e "s^USER_GID^$$(id -g)^" \
	       < docker/docker-compose.yml-tmpl > docker/docker-compose.yml

run: docker/docker_compose.yml clean
	docker-compose -f ./docker/docker-compose.yml up -d
	cd docker && docker-compose logs tiledb

clean:
	docker-compose -f ./docker/docker-compose.yml down

