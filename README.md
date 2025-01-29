# install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd microjson
poetry install
cd ..

# prepare image tiles for ld
python make_isbn_images_fractal_cluster.py -x _cluster -o images_tmp
python make_isbn_images_2_tiling.py --input images_tmp --suffix cluster --depth one --output images -t 512 --move-dir ../isbn_images_data/images --move-suffix=''
python make_isbn_images_2_tiling.py --input images_tmp --suffix cluster --depth one --output images -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 2
python make_isbn_images_2_tiling.py --input images_tmp --suffix cluster --depth one --output images -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 4
python make_isbn_images_2_tiling.py --input images_tmp --suffix cluster --depth one --output images -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 8
python make_isbn_images_2_tiling.py --input images_tmp --suffix cluster --depth one --output images -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 16
python make_isbn_images_2_tiling.py --input images_tmp --suffix cluster --depth one --output images -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 32



# prepare vector tiles for ld
python make_isbn_json.py -o data_ld.json --max-prefix-len 6 --scale 32 --label-point
cd microjson/src/microjson/examples
# TODO : make nicer when microjson is released on pypi
poetry run python tiling_isbn.py ../../../../data_ld.json ../../../../../isbn_images_data/vt_ld ld true


python make_isbn_images_fractal.py -x _hd -o images_tmp
python make_isbn_images_2_tiling.py --input images_tmp --suffix hd --depth one --output images_tmp -t 512 --move-dir ../isbn_images_data/images --move-suffix=''
python make_isbn_images_2_tiling.py --input images_tmp --suffix hd --depth one --output images_tmp -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 2
python make_isbn_images_2_tiling.py --input images_tmp --suffix hd --depth one --output images_tmp -t 512 --move-dir ../isbn_images_data/images --move-suffix='' -r 4


python make_isbn_json.py -o data_hd.json --max-prefix-len 9 --scale 4 --hd --label-point
poetry run python tiling_isbn.py ../../../../data_ld.json ../../../../../isbn_images_data/vt_hd hd true

