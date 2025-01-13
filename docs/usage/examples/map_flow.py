from dynaflow import DynaFlow

FLOW = {
    "StartAt": "MapState",
    "States": {
        "MapState": {
            "Type": "Map",
            "InputPath": "$",
            "Parameters": "$.carts",
            "ItemsPath": "$",
            "ResultPath": "$.result",
            "OutputPath": "$.result",
            "ItemProcessor": {
                "StartAt": "GetItemsForPromotion",
                "States": {
                    "GetItemsForPromotion": {
                        "Type": "Pass",
                        "InputPath": "$",
                        "OutputPath": "$.items[?(@.price > 100)].name",
                        "End": True,
                    }
                },
            },
            "End": True,
        }
    },
}


def exec_with_simple_function_db():

    executor = DynaFlow(FLOW, {}, lambda db, params: db[params["Name"]])

    print(
        "\tFLOW_EXECUTION_RESULT:",
        executor.run(
            {
                "carts": [
                    {
                        "items": [
                            {"name": "item1", "price": 50},
                            {"name": "item2", "price": 150},
                            {"name": "item3", "price": 200},
                        ]
                    },
                    {"items": [{"name": "item2", "price": 150}]},
                ]
            }
        ),
    )


if __name__ == "__main__":
    exec_with_simple_function_db()
