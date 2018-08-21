# python ds_poll.py  # https disabled
# python3 ds_poll.py -o localhost:8843 -s -v #https enabled
python3 ds_poll.py -q queue_server:8001 -o datashield_opal:8443 -s -v # start in dockerd