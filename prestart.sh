#! /usr/bin/env bash

# Download the custom script if provided
if  [ -z $USER_SCRIPT ] ;
then
    echo "no user script provided, using default"
else
    wget $USER_SCRIPT -q -O /app/custom_service.py
fi
# Download the model
echo "downloading model"
wget $MODEL_PATH -q -O /app/model.m
echo "starting web server"