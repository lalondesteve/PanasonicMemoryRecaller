from htpy import (
    article,
    h3,
    h5,
    pre,
    code,
    form,
    div,
    select,
    option,
    label,
    button,
    input,
    legend,
    Renderable,
)


def projector_card(projector) -> Renderable:
    _form = form(".row", hx_post="/projector/recall")[
        div(".max .field .border .label")[
            select("#memory", name="memory")[(option[x] for x in range(1, 11))],
            label["select memory"],
        ],
        button(".small-round .max", type="submit")["Recall"],
    ]

    return article(".card")[
        h3[projector.name],
        h5(".primary-text")[projector.ip],
        pre(".large-elevate")[code("#last-message")[projector.last_message]],
        _form,
    ]


def add_projector_button() -> Renderable:
    return div(".max .right-align .")[
        button(".small-round .max", hx_get="/projectors/add")["Add Projector"]
    ]


def edit_card(projector) -> Renderable:
    return article(".card")[
        form(
            hx_post="/projectors",
            hx_on="::after-request='if(event.detail.successful) this.reset()'",
        )[
            legend["Update projector"],
            input(type="hidden", id="id", name="id", value=projector.id),
            div(".field .border .label")[
                input("#name", name="name", value=projector.name),
                label["Name"],
            ],
            div(".field .border .label")[
                input("#ip", name="ip", value=projector.ip),
                label["IP Address"],
            ],
            button(".small-round .max", type="submit")["Update"],
        ]
    ]
