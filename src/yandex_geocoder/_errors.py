from pydantic import ValidationError


def handle_query_exception(
        exc: ValidationError,
) -> str:
    messages = []

    for error in exc.errors():
        field = ".".join(
            str(item)
            for item in error["loc"]
        )

        match error["type"]:

            case "extra_forbidden":
                messages.append(
                    f"Unknown parameter `{field}`"
                )

            case "missing":
                messages.append(
                    f"Required parameter `{field}` is missing"
                )

            case _:
                messages.append(
                    f"{field}: {error['msg']}"
                )

    return "; ".join(messages)
