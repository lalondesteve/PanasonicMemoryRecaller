from htpy import (
    article,
    h3,
    h5,
    html,
    head,
    meta,
    title,
    script,
    link,
    body,
    nav,
    header,
    a,
    i,
    main,
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

from markupsafe import Markup


def get_html(main: Renderable):
    return html(lang="en")[
        head[
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=devide-width, initial-scale=1"),
            title()["Panasonic Memory Recaller"],
            link(href="/static/beercss/beer.min.css", rel="stylesheet"),
            script(type="module", src="static/beercss/beer.min.js"),
            script(type="module", src="static/beercss/material-dynamic-colors.min.js"),
            script(src="/static/htmx.min.js"),
            link(rel="stylesheet", href="/static/style.css"),
        ],
        get_body(main),
        get_script(),
    ]


def get_body(main: Renderable):
    return body(".dark")[get_nav(), main]


def get_nav():
    return nav(".top .middle-align")[
        header()[h5["Panasonic Memory Recaller"]],
        header(".max .right-align .primary-text")[
            a(href="/")[i(".primary-text .border .small-round .tiny-padding")["home"]],
            a(href="/edit")[
                i(".primary-text .border .small-round .tiny-padding")["widgets"]
            ],
        ],
    ]


def get_index():
    return main(".responsive", hx_boost="true")[
        div("#projector-component", hx_get="/projectors", hx_trigger="load")[
            "loading projectors"
        ],
        get_edit_section(),
    ]


def get_edit():
    return main(".responsive", hx_boost="true")[get_edit_section()]


def get_edit_section():
    return (
        div("#edit", hx_trigger="load", hx_get="/projector-edit")["loading projectors"],
    )


def get_script():
    return str(
        script(type="text/javascript")[
            Markup(
                """
                function theme(color){ 
                ui("theme", "#009fff");
                ui("mode", "dark")
                }
                window.addEventListener("DOMContentLoaded", ()=>theme());
                """
            )
        ]
    )


def projector_card(projector) -> Renderable:
    _form = form(".row .flex", hx_post="/projector/recall")[
        input(type="hidden", id="id", name="id", value=projector.id),
        div(".max .field .border .label")[
            select("#memory", name="memory")[(option[x] for x in range(1, 11))],
            label["select memory"],
        ],
        button(".small-round", type="submit")["Recall"],
    ]

    return article(".card")[
        h3[projector.name],
        h5(".primary-text")[projector.ip],
        pre("#last-message .large-elevate")[code[projector.last_message]],
        _form,
    ]


def add_projector_button() -> Renderable:
    return div("#add-button .max .right-align ")[
        button(".small-round .max", hx_post="/projector-edit", hx_target="#edit")[
            "Add Projector"
        ]
    ]


def edit_card(projector) -> Renderable:
    return article(".card")[
        form(
            hx_post="/projectors",
            hx_on="::after-request='if(event.detail.successful) alert()",
            hx_target="#projector-component",
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
            div(".max")[
                button(".small-round", type="submit")["Update"],
                button(
                    ".small-round .error .right-align",
                    hx_confirm="Are you sure you want to delete the projector?",
                    hx_delete="/projector-edit",
                    hx_target="#edit",
                )["Delete"],
            ],
        ]
    ]
