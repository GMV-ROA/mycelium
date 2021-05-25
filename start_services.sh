#!/bin/bash

echo "Starting Mycelium services"

if  [[ !$(systemctl is-active --quiet mavlink-router.service) ]]; then
    sudo systemctl start mavlink-router.service
fi

if  [[ !$(systemctl is-active --quiet redis.service) ]]; then
    sudo systemctl start redis.service
fi

if  [[ !$(systemctl is-active --quiet mycelium-t265.service) ]]; then
    sudo systemctl start mycelium-t265.service
fi

if  [[ !$(systemctl is-active --quiet mycelium-d435.service) ]]; then
    sudo systemctl start mycelium-d435.service
fi

if  [[ !$(systemctl is-active --quiet mycelium-instrument-redis.service) ]]; then
    sudo systemctl start mycelium-instrument-redis.service
fi

if  [[ !$(systemctl is-active --quiet mycelium-ap-redis.service) ]]; then
    sudo systemctl start mycelium-ap-redis.service
fi

echo "Mycelium services running"
