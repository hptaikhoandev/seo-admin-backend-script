ec2_params = [
    {
        "team": "admin", 
        "region": "ap-northeast-1", 
        "subnet_id": "subnet-073832dee4d971c43",
        "security_group_id": 
            [
                "sg-03e78ced7e58cae7c",
                "sg-0fdeede3c870cd3f2",
                "sg-0d0a0ffe0169b71c9",
                "sg-069d0dd3042999748",
                "sg-0bb8718d8a6680ff1",
            ],
        "key_name": "pro-seoadmin-ap-northeast-1-key-pair-admin",
        "instance_type": "t2.micro",
        "ami_id": "ami-005fb99af5d106c31",
    },
    {
        "team": "seo-1", 
        "region": "us-east-1", 
        "subnet_id": "subnet-066de010d542a6b6e",
        "security_group_id": 
            [
                "sg-02084bd15de0ef9e9",
                "sg-0c41dee00f9753c63",
            ],
        "key_name": "pro-seoadmin-us-east-1-key-pair-seo-4-01",
        "instance_type": "c5.xlarge",
        "ami_id": "ami-0f2192f7e94a3cb97",
    },
    {
        "team": "seo-4", 
        "region": "us-east-1", 
        "subnet_id": "subnet-016fa59cc04d019c7",
        "security_group_id": 
            [
                "sg-0c177e5fd1d6aa366",
                "sg-0ccd5d90566b55eef",
                "sg-035b52364640a4fd5",
                "sg-0eaa510abc3ff18af",
            ],
        "key_name": "pro-seoadmin-us-east-1-key-pair-seo-4-01",
        "instance_type": "c5.xlarge",
        "ami_id": "ami-0f2192f7e94a3cb97",
    },
    {
        "team": "seo-2", 
        "region": "ap-southeast-2", 
        "subnet_id": "subnet-0f1f6c5f023aa00a5",
        "security_group_id": 
            [
                "sg-078697afe0b73e1a1",
                "sg-0106be2228effe847",
                "sg-06ccd62938102b9f4",
                "sg-08367b99b090d8648",
                "sg-06b2f7d09997b8cde",
            ],
        "key_name": "pro-seoadmin-ap-southeast-2-key-pair-seo",
        "instance_type": "c5.xlarge",
        "ami_id": "ami-06066b38c477ac335",
    },
    {
        "team": "seo-3", 
        "region": "ap-southeast-2", 
        "subnet_id": "subnet-0eeaecec7443b334a",
        "security_group_id": 
            [
                "sg-0e11f79eaecab813d",
                "sg-02471248ad33f40cc",
                "sg-0b703ae78296375cd",
                "sg-0d78adeff861d762f",
            ],
        "key_name": "pro-seoadmin-ap-southeast-2-key-pair-seo",
        "instance_type": "c5.xlarge",
        "ami_id": "ami-06066b38c477ac335",
    },
    {
        "team": "seo-5", 
        "region": "ap-southeast-1", 
        "subnet_id": "subnet-01cfba23cccb3d8eb",
        "security_group_id": 
            [
                "sg-0a32e6c5a29553892",
                "sg-06994974b65f78dd7",
                "sg-02ee3d409ea20f86a",
                "sg-0bf527ca51678375a",
                "sg-0451a0175a1ebdd13",
            ],
        "key_name": "pro-seoadmin-ap-southeast-1-key-pair-seo",
        "instance_type": "c5.xlarge",
        "ami_id": "ami-00815fbf5fe0ff857",
    },
    {
        "team": "seo-6", 
        "region": "ap-southeast-1", 
        "subnet_id": "subnet-0a0af7770d9001681",
        "security_group_id": 
            [
                "sg-03eea6c2c1006f7a7",
                "sg-00f470495fdcdd1e9",
                "sg-0cee047553fac39f6",
                "sg-07e98f11f594a679d",
                "sg-070fa60543dfef403",
            ],
        "key_name": "pro-seoadmin-ap-southeast-1-key-pair-seo",
        "instance_type": "c5.xlarge",
        "ami_id": "ami-00815fbf5fe0ff857",
    },
]

