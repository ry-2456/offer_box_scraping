[ ! -d data ] && mkdir data

docker build -t offerbox_scraping:1.0 .
docker run -it --rm -v $(pwd):/workdir offerbox_scraping:1.0
