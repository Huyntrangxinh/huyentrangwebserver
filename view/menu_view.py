# menu_view.py

class MenuView:
    def show_menu(self, menu_items):
        """
        Return simple HTML showing all menu items.
        """
        html_content = """
        <html>
        <head>
            <title>Our Menu</title>
        </head>
        <body>
            <h1>Menu</h1>
            <ul>
        """

        for item in menu_items:
            html_content += f"""
                <li>
                    <strong>{item['name']}</strong> - ${item['price']:.2f}<br>
                    <em>{item['description']}</em>
                </li>
            """

        html_content += """
            </ul>
        </body>
        </html>
        """
        return html_content
