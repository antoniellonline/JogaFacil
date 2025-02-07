import flet as ft
import sqlite3
from datetime import datetime
import os

class Player:
    def __init__(self, name, goals=0):
        self.name = name
        self.goals = goals

class GoalTrackerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "⚽ GoalMaster Pro"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.page.window.width = 400
        self.page.window.height = 700
        self.dialog = None  # Referência única para o diálogo
        self.setup_db()
        self.main_ui()

    def setup_db(self):
        db_path = os.path.join(os.path.dirname(__file__), "goal_tracker.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS players
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT UNIQUE,
                     goals INTEGER,
                     created_at TEXT)''')
        self.conn.commit()
    def main_ui(self):
        # Header
        self.header = ft.Text("GoalMaster Pro ⚽", size=24, weight=ft.FontWeight.BOLD)
        
        # Add Player Section
        self.new_player = ft.TextField(
            label="Nome do Jogador",
            expand=True,
            border_color=ft.Colors.GREEN_400,
            autofocus=True
        )
        
        self.add_button = ft.FloatingActionButton(
            icon=ft.Icons.PERSON_ADD,
            bgcolor=ft.Colors.GREEN_400,
            on_click=self.add_player
        )
        
        # Players List
        self.players_list = ft.ListView(expand=True, spacing=10)
        
        # Stats Section
        self.stats = ft.Row([
            ft.IconButton(ft.Icons.INSERT_CHART_OUTLINED, on_click=self.show_stats),
            ft.IconButton(ft.Icons.EMOJI_EVENTS, on_click=self.show_top_scorers),  # Ícone válido
            ft.IconButton(ft.Icons.HISTORY, on_click=self.show_history)
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        
        # Assemble UI
        self.page.add(
            ft.Column([
                self.header,
                ft.Row([self.new_player, self.add_button]),
                ft.Divider(height=20),
                self.players_list,
                self.stats
            ])
        )
        self.load_players()

    def player_card(self, player):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON_OUTLINE, color=ft.Colors.BLUE_200),
                ft.Column([
                    ft.Text(player.name, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Gols: {player.goals}", color=ft.Colors.GREEN_300)
                ], expand=True),
                ft.IconButton(
                    icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    on_click=lambda e: self.update_goals(player.name, -1)
                ),
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    icon_color=ft.Colors.GREEN_400,
                    on_click=lambda e: self.update_goals(player.name, 1)
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_FOREVER,
                    icon_color=ft.Colors.RED_700,
                    on_click=lambda e: self.delete_player(player.name)
                )
            ]),
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=10,
            border_radius=10,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        )

    def load_players(self):
        self.players_list.controls.clear()
        c = self.conn.cursor()
        c.execute("SELECT name, goals FROM players ORDER BY goals DESC")
        for name, goals in c.fetchall():
            self.players_list.controls.append(self.player_card(Player(name, goals)))
        self.page.update()

    def add_player(self, e):
        name = self.new_player.value.strip()
        if not name:
            return
        
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO players (name, goals, created_at) VALUES (?, ?, ?)",
                     (name, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
            self.new_player.value = ""
            self.load_players()
        except sqlite3.IntegrityError:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Jogador já existe!"),
                bgcolor=ft.Colors.RED_800
            )
            self.page.snack_bar.open = True
            self.page.update()

    def update_goals(self, name, delta):
        c = self.conn.cursor()
        c.execute("UPDATE players SET goals = MAX(goals + ?, 0) WHERE name = ?", (delta, name))
        self.conn.commit()
        self.load_players()

    
    def delete_player(self, name):
        def confirm_delete(e):
            c = self.conn.cursor()
            c.execute("DELETE FROM players WHERE name = ?", (name,))
            self.conn.commit()
            self.load_players()
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Excluir permanentemente {name}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, "open", False)),
                ft.TextButton("Excluir", on_click=confirm_delete)
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_top_scorers(self, e):
        c = self.conn.cursor()
        c.execute("SELECT name, goals FROM players ORDER BY goals DESC LIMIT 5")
        players = c.fetchall()

        items = []
        for idx, (name, goals) in enumerate(players):
            items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.MILITARY_TECH,
                                  color=self.medal_color(idx)),
                    title=ft.Text(name),
                    subtitle=ft.Text(f"{goals} gols"),
                    trailing=ft.Text(f"#{idx+1}", 
                                   color=self.medal_color(idx))
                )
            )

        self.dialog = ft.AlertDialog(
            title=ft.Text("Top Artilheiros 🏆"),
            content=ft.Column(items, tight=True),
            actions=[
                ft.TextButton("OK", on_click=self.close_dialog)
            ]
        )
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def show_stats(self, e):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*), SUM(goals) FROM players")
        total_players, total_goals = c.fetchone()

        stats_content = ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PEOPLE_OUTLINE),
                title=ft.Text("Jogadores Cadastrados"),
                trailing=ft.Text(str(total_players))
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.SPORTS_SCORE),
                title=ft.Text("Total de Gols"),
                trailing=ft.Text(str(total_goals or 0))
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.TIMER),
                title=ft.Text("Média de Gols/Jogador"),
                trailing=ft.Text(f"{total_goals/total_players:.1f}" if total_players else "0.0")
            )
        ])

        self.dialog = ft.AlertDialog(
            title=ft.Text("Estatísticas 📊"),
            content=stats_content,
            actions=[ft.TextButton("OK", on_click=self.close_dialog)]
        )
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def show_history(self, e):
        c = self.conn.cursor()
        c.execute("SELECT name, created_at FROM players ORDER BY created_at DESC")
        history = c.fetchall()

        items = []
        for name, created_at in history:
            items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.HISTORY),
                    title=ft.Text(name),
                    subtitle=ft.Text(created_at)
                )
            )

        self.dialog = ft.AlertDialog(
            title=ft.Text("Histórico de Cadastro 📅"),
            content=ft.Column(items, height=300),
            actions=[ft.TextButton("OK", on_click=self.close_dialog)]
        )
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def close_dialog(self, e):
        self.dialog.open = False
        self.page.update()

    def delete_player(self, name):
        def confirm_delete(e):
            c = self.conn.cursor()
            c.execute("DELETE FROM players WHERE name = ?", (name,))
            self.conn.commit()
            self.load_players()
            self.dialog.open = False
            self.page.update()

        self.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Excluir permanentemente {name}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dialog),
                ft.TextButton("Excluir", on_click=confirm_delete)
            ]
        )
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

def main(page: ft.Page):
    GoalTrackerApp(page)

ft.app(target=main, assets_dir="assets")