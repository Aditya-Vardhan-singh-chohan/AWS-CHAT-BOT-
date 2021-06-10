import boto3

# Get the service resource.
dynamodb = boto3.resource("dynamodb")

# Create the DynamoDB table.
game_table = dynamodb.create_table(
    TableName="disastle_game",
    KeySchema=[
        {"AttributeName": "id", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"},
    ],
    AttributeDefinitions=[
        {"AttributeName": "id", "AttributeType": "S"},
        {"AttributeName": "timestamp", "AttributeType": "N"},
    ],
    ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
)

# Wait until the table exists.
game_table.meta.client.get_waiter("table_exists").wait(
    TableName="disastle_game"
)
