""" COLORS """
GREY_0 = "#2A2A2A"
GREY_1 = "#323232"
GREY_2 = "#4D4D4D"
GREY_3 = "#656565"
GREY_4 = "#6F6F6F"

WHITE = "#FFFFFF"
WHITE_GRAY = "#F2F2F2"

GREEN_1 = "#0A6160"
GREEN_2 = "#0C8371"

BLUE_0 = "#005588"
BLUE_1 = "#0077AA"

RED_1 = "#FF0055"
RED_2 = "#E60000"

ORANGE_0 = "#FF9900"
ORANGE_1 = "#FFAD33"

""" CANVAS AND GRAPH STYLESHEETS """
VIEW_STYLE = ("QGraphicsView {"
              "border: 1px solid " + GREY_2 + ";" +
              "background-color: " + GREY_3 + ";" +
              "}")

CANVAS_STYLE = ("background-color: " + GREY_3 + ";" +
                "border: none;"
                "QMenu {"
                "border: 2px solid " + GREY_1 + ";" +
                "border-radius: 0px;"
                "color: white;"
                "padding: 0px;"
                "background-color: " + GREY_2 + ";" +
                "}"
                "QMenu:selected {"
                "background-color: " + GREEN_2 + ";" +
                "}")

GRAPHIC_BLOCK_STYLE = ("QWidget {"
                       "background-color: " + GREY_1 + ";" +
                       "border: 2px solid " + GREY_0 + ";" +
                       "border-bottom-left-radius: 10px;"
                       "border-bottom-right-radius: 10px;"
                       "padding: 2px;"
                       "}"
                       "QMenu {"
                       "border: 2px solid " + GREY_1 + ";" +
                       "border-radius: 0px;"
                       "color: white;"
                       "background-color: " + GREY_2 + ";" +
                       "padding: 0px;"
                       "}"
                       "QMenu:selected {"
                       "background-color: " + GREEN_2 + ";" +
                       "}")

""" LABELS STYLESHEETS """
NODE_TITLE_STYLE = ("QLabel {"
                    "color: white;"
                    "background-color: " + BLUE_0 + ";" +
                    "margin-bottom: -5px;"  # Overwrites double margin
                    "padding: 7px;"
                    "font-family: georgia;"
                    "font-size: 18px;"
                    "border-top-left-radius: 10px;"
                    "border-top-right-radius: 10px;"
                    "border-bottom-left-radius: 0px;"
                    "border-bottom-right-radius: 0px;"
                    "}"
                    "QLabel:hover {"
                    "background-color: " + BLUE_1 + ";" +
                    "}")

PROPERTY_CONDITION_STYLE = ("QLabel {"
                            "color: white;"
                            "background-color: " + RED_2 + ";" +
                            "margin-bottom: -5px;"
                            "padding-left: 7px;"
                            "font-family: calibri;"
                            "font-size: 12px;"
                            "border-bottom-left-radius: 0px;"
                            "border-bottom-right-radius: 0px;"
                            "}")

PROPERTY_TITLE_STYLE = ("QLabel {"
                        "color: white;"
                        "background-color: " + ORANGE_0 + ";" +
                        "margin-bottom: -5px;"
                        "padding: 7px;"
                        "font-family: georgia;"
                        "font-size: 18px;"
                        "border-top-left-radius: 10px;"
                        "border-top-right-radius: 30px;"
                        "border-bottom-left-radius: 0px;"
                        "border-bottom-right-radius: 0px;"
                        "}"
                        "QLabel:hover {"
                        "background-color: " + ORANGE_1 + ";" +
                        "}")

EMPTY_NODE_TITLE = ("QLabel {"
                    "color: white;"
                    "background-color: #005588;"
                    "padding: 7px;"
                    "font-family: calibri;"
                    "font-size: 18px;"
                    "border-radius: 10px;"
                    "}"
                    "QLabel:hover {"
                    "background-color: #0077AA;"
                    "}")

PAR_NODE_STYLE = ("border: none;"
                  "border-radius: 0px;"
                  "color: white;"
                  "font-weight: bold;"
                  "font-family: calibri;")

DIM_NODE_STYLE = ("border: none;"
                  "border-radius: 0px;"
                  "font-family: calibri;"
                  "color: " + GREY_4 + ";")

""" BLOCKS_LIST STYLESHEET """
NODE_LABEL_STYLE = ("QLabel {"
                    "color: white;"
                    "background-color: " + GREEN_1 + ";" +
                    "text-transform: uppercase;"
                    "margin: 5px;"
                    "padding: 4px;"
                    "font-weight: bold;"
                    "max-height: 17px;"
                    "}")

HIDDEN_LABEL_STYLE = ("height: 0px;"
                      "color: rgba(0, 0, 0, 0);"
                      "background-color: none;"
                      "padding: 0px;"
                      "margin: 0px;"
                      "font-size: 1px;"
                      "border: none")

ERROR_LABEL_STYLE = ("QLabel {"
                     "color: white;"
                     "background-color: " + RED_1 + ";" +
                     "text-transform: uppercase;"
                     "margin: 5px;"
                     "padding: 4px;"
                     "font-weight: bold;"
                     "}")

BUTTON_STYLE = ("QPushButton { "
                "background-color: " + GREY_2 + ";" +
                "border: 2px solid " + GREY_1 + ";" +
                "padding: 6px;"
                "color: #CFCFCF;"
                "font-family: georgia;"
                "border-radius: 5px;"
                "margin: 2px;"
                "}"
                "QPushButton:hover {"
                "background-color: " + GREY_4 + ";" +
                "border: 2px solid " + GREY_3 + ";" +
                "font-weight: bold;"
                "color: white;"
                "}"
                "QToolTip {"
                "background-color: " + GREY_1 + ";" +
                "color: white;"
                "border: black solid 1px;"
                "}")

PRIMARY_BUTTON_STYLE = ("QPushButton { "
                        "background-color: " + GREEN_2 + ";" +
                        "border: 2px solid " + GREEN_1 + ";" +
                        "padding: 6px;"
                        "color: #CFCFCF;"
                        "font-family: georgia;"
                        "border-radius: 5px;"
                        "margin: 2px;"
                        "}"
                        "QPushButton:hover {"
                        "background-color: " + GREEN_1 + ";" +
                        "border: 2px solid " + GREEN_2 + ";" +
                        "font-weight: bold;"
                        "color: white;"
                        "}"
                        "QToolTip {"
                        "background-color: " + GREY_1 + ";" +
                        "color: white;"
                        "border: black solid 1px;"
                        "}")

TOOLBAR_STYLE = ("background-color: " + GREY_1 + ";" +
                 "padding: 4px;"
                 "QToolBar {"
                 "border: 1px solid " + GREY_2 + ";" +
                 "}"
                 "QToolBar::separator {"
                 "height: 2px;"
                 "background-color: " + GREY_2 + ";" +
                 "}")

TITLE_LABEL_STYLE = ("color: white;"
                     "font-size: 15px;"
                     "margin-bottom: 3px;"
                     "font-weight: bold;"
                     "font-family: georgia;"
                     "padding: 5px;"
                     "border-bottom: 2px solid " + GREY_2 + ";")

VALUE_LABEL_STYLE = ("color: white;"
                     "background-color: " + GREY_2 + ";" +
                     "text-align: left;"
                     "border: none;"
                     "padding: 2px;"
                     "QLineEdit::placeholder {"
                     "color: " + GREY_4 + ";" +
                     "}")

UNEDITABLE_VALUE_LABEL_STYLE = ("color: white;"
                                "text-align: left;"
                                "border: none;")

NOT_ACCEPTABLE_INPUT = ("color: white;"
                        "background-color: " + RED_2 + ";" +
                        "text-align: left;"
                        "border: none;"
                        "padding: 2px;"
                        "QLineEdit::placeholder {"
                        "color: " + GREY_4 + ";" +
                        "}")

PARAM_LABEL_STYLE = ("color: white;"
                     "border: none;"
                     "padding: 2px 0px 2px 2px;")

UNEDITABLE_PARAM_LABEL_STYLE = ("color: " + GREEN_2 + ";" +
                                "padding: 2px 0px 2px 2px;"
                                "font-weight: bold;")

IN_DIM_LABEL_STYLE = ("color: white;"
                      "border: none;"
                      "border-bottom: 2px solid " + GREEN_1 + ";" +
                      "padding: 2px 0px 2px 2px;"
                      "font-weight: bold;"
                      "text-transform: uppercase;"
                      )

MENU_BAR_STYLE = ("QMenuBar, QMenu {"
                  "color: white;"
                  "background-color: " + GREY_1 + ";" +
                  "border: 1px solid " + GREY_2 + ";" +
                  "}"
                  "QMenuBar::item:selected {"
                  "background-color: " + GREY_2 + ";" +
                  "}"
                  "QMenuBar::item:pressed, QMenu::item:selected {"
                  "background-color: " + GREEN_2 + ";" +
                  "}"
                  "QMenu::separator {"
                  "height: 2px;"
                  "background-color: " + GREY_2 + ";" +
                  "}")

""" DIALOGS STYLESHEET """
DIALOG_STYLE = ("background-color: " + GREY_1 + ";")

RADIO_BUTTON_STYLE = ("color: white;"
                      "padding-left: 20px;")

""" STATUS BAR """
STATUS_BAR_STYLE = ("QStatusBar {"
                    "background-color: " + GREY_1 + ";" +
                    "border: 2px solid " + GREY_2 + ";" +
                    "}"
                    "QStatusBar::item {"
                    "border: None;"
                    "}")

STATUS_BAR_WIDGET_STYLE = ("color: " + GREY_4 + ";" +
                           "font-family: georgia;"
                           "padding: 1px;"
                           "border-right: 1px solid " + GREY_2)

""" PARAMETERS BOX """

PAR_NAME_LABEL = ("color: white;"
                  "background-color: " + GREY_2 + ";" +
                  "font-weight: bold;"
                  "font-family: calibri;"
                  "font-size: 13px;"
                  "margin: 5px")

DESCRIPTION_STYLE = ("color: white;"
                     "border: none;"
                     "margin: 5px;")

DOCK_STYLE = ("color: " + GREEN_2 + ";" +
              "margin: 0;"
              "padding: 0;")

SCROLL_AREA_STYLE = ("background-color: " + GREY_1 + ";" +
                     "border: none")

VERTICAL_SCROLL_BAR = ("background-color: " + GREY_1 + ";" +
                       "border: none")

HORIZONTAL_SCROLL_BAR = ("QScrollBar::handle:horizontal {"
                         "background-color: " + GREY_1 + ";" +
                         "border: 2px solid " + GREY_2 + ";" +
                         "}")

BLOCK_BOX_STYLE = ("background-color: " + GREY_1 + ";" +
                   "border: none")

DROPDOWN_STYLE = ("border-bottom: 2px solid " + GREY_2 + ";" +
                  "padding: 0px;")

DROPDOWN_TOP_STYLE = ("padding: 0px;"
                      "margin: 0px;"
                      "max-height: 20px;"
                      "vertical-align: center;")

DROPDOWN_NAME_STYLE = ("color: white;"
                       "font-family: georgia;"
                       "font-weight: bold;"
                       "padding-top: 2px;"
                       "text-transform: uppercase;"
                       "background-color: " + GREY_3 + ";")

DROPDOWN_TYPE_STYLE = ("color: white;"
                       "font-family: georgia;"
                       "height: auto;"
                       "padding: 0px;"
                       "max-width: 90%;")

DROPDOWN_DEFAULT_STYLE = ("color: " + GREY_1 + ";" +
                          "background-color: " + GREEN_2 + ";" +
                          "font-family: georgia;"
                          "max-width: 60%;"
                          "height: auto;"
                          "font-weight: bold;"
                          "text-align: center;")

DROPDOWN_ARROW_STYLE = ("background-color: none;"
                        "color: " + GREY_4 + ";" +
                        "height: auto;"
                        "max-width: auto;")

""" LOADING DIALOG """
LOADING_LABEL_STYLE = ("text-align: center;"
                       "font-family: georgia;"
                       "color: white;")

PROGRESS_BAR_STYLE = ("#ProgressBar {"
                      "border: 2px solid " + GREY_1 + ";" +
                      "border-radius: 5px;"
                      "background-color: " + GREY_2 + ";" +
                      "}"
                      "#ProgressBar::chunk {"
                      "background-color: " + GREEN_2 + ";" +
                      "width: 10px;"
                      "margin: 0.5px;"
                      "}")
