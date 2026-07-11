"""
Consultas agregadas para el dashboard y la página de estadísticas.
"""
from datetime import datetime, timedelta

from db.connection import get_db_connection


def obtener_datos_inicio():
    """Datos resumidos para la página de inicio (dashboard)."""
    hoy = datetime.now().date().isoformat()
    with get_db_connection() as conn:
        cur = conn.cursor()
        total_clientes = cur.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        total_disciplinas = cur.execute("SELECT COUNT(*) FROM disciplinas").fetchone()[0]
        accesos_hoy = cur.execute("""
            SELECT COUNT(*) FROM logs
            WHERE tipo='ACCESO' AND resultado='EXITO'
            AND fecha >= ? || ' 00:00:00'
        """, (hoy,)).fetchone()[0]
        denegados_hoy = cur.execute("""
            SELECT COUNT(*) FROM logs
            WHERE tipo='ACCESO' AND resultado='DENEGADO'
            AND fecha >= ? || ' 00:00:00'
        """, (hoy,)).fetchone()[0]
        vencimientos_proximos = cur.execute("""
            SELECT COUNT(*) FROM clientes
            WHERE vencimiento IS NOT NULL
            AND vencimiento BETWEEN ? AND date(?, '+30 days')
        """, (hoy, hoy)).fetchone()[0]
        clientes_vencidos = cur.execute("""
            SELECT COUNT(*) FROM clientes
            WHERE vencimiento IS NOT NULL AND vencimiento < ?
        """, (hoy,)).fetchone()[0]
    return {
        "total_clientes": total_clientes,
        "total_disciplinas": total_disciplinas,
        "accesos_hoy": accesos_hoy,
        "denegados_hoy": denegados_hoy,
        "vencimientos_proximos": vencimientos_proximos,
        "clientes_vencidos": clientes_vencidos,
    }


def obtener_estadisticas():
    """Devuelve datos agregados para la página de estadísticas."""
    hoy = datetime.now().date()
    mes_inicio = hoy.replace(day=1).isoformat()
    hoy_iso = hoy.isoformat()

    with get_db_connection() as conn:
        cur = conn.cursor()

        total_clientes = cur.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        accesos_hoy = cur.execute(
            "SELECT COUNT(*) FROM logs WHERE tipo='ACCESO' AND resultado='EXITO' AND fecha >= ? || ' 00:00:00'",
            (hoy_iso,)
        ).fetchone()[0]
        accesos_mes = cur.execute(
            "SELECT COUNT(*) FROM logs WHERE tipo='ACCESO' AND resultado='EXITO' AND fecha >= ? || ' 00:00:00'",
            (mes_inicio,)
        ).fetchone()[0]
        denegados_mes = cur.execute(
            "SELECT COUNT(*) FROM logs WHERE tipo='ACCESO' AND resultado='DENEGADO' AND fecha >= ? || ' 00:00:00'",
            (mes_inicio,)
        ).fetchone()[0]
        clientes_vencidos = cur.execute(
            "SELECT COUNT(*) FROM clientes WHERE vencimiento IS NOT NULL AND vencimiento < ?",
            (hoy_iso,)
        ).fetchone()[0]

        hora_pico_row = cur.execute("""
            SELECT substr(fecha, 12, 2) as hora, COUNT(*) as cnt
            FROM logs WHERE tipo='ACCESO' AND resultado='EXITO'
            GROUP BY hora ORDER BY cnt DESC LIMIT 1
        """).fetchone()
        hora_pico = (hora_pico_row[0] + ":00") if hora_pico_row else "--"

        dias_rows = cur.execute("""
            SELECT strftime('%w', fecha) as dow, COUNT(*) as cnt
            FROM logs WHERE tipo='ACCESO' AND resultado='EXITO'
            GROUP BY dow
        """).fetchall()
        dias_map = {r[0]: r[1] for r in dias_rows}
        dias_semana_labels = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
        dias_semana_data = [dias_map.get(str(i), 0) for i in range(7)]

        horas_rows = cur.execute("""
            SELECT substr(fecha, 12, 2) as hora, COUNT(*) as cnt
            FROM logs WHERE tipo='ACCESO' AND resultado='EXITO'
            GROUP BY hora ORDER BY hora
        """).fetchall()
        horas_labels = [r[0] + ":00" for r in horas_rows]
        horas_data = [r[1] for r in horas_rows]

        top_rows = cur.execute(
            """
            SELECT c.nombre || ' ' || COALESCE(c.apellido, '') as nombre, COUNT(*) as cnt
            FROM logs l JOIN clientes c ON l.cliente_id = c.id
            WHERE l.tipo='ACCESO' AND l.resultado='EXITO'
            AND l.fecha >= ? || ' 00:00:00'
            GROUP BY l.cliente_id ORDER BY cnt DESC LIMIT 10
        """,
            (mes_inicio,)
        ).fetchall()
        top_clientes_nombres = [r[0].strip() for r in top_rows]
        top_clientes_counts = [r[1] for r in top_rows]

        res_rows = cur.execute(
            """
            SELECT resultado, COUNT(*) FROM logs
            WHERE tipo='ACCESO'
            AND fecha >= ? || ' 00:00:00'
            GROUP BY resultado
        """,
            (mes_inicio,)
        ).fetchall()
        resultados_labels = [r[0] for r in res_rows]
        resultados_data = [r[1] for r in res_rows]

        # Últimos 14 días (renombramos la variable 'l' por 'item')
        linea = []
        for i in range(13, -1, -1):
            dia = (hoy - timedelta(days=i)).isoformat()
            cnt = cur.execute(
                """
                SELECT COUNT(*) FROM logs
                WHERE tipo='ACCESO' AND resultado='EXITO'
                AND fecha >= ? || ' 00:00:00' AND fecha < ? || ' 23:59:59'
            """,
                (dia, dia)
            ).fetchone()[0]
            linea.append((dia[5:], cnt))
        linea_labels = [item[0] for item in linea]
        linea_data = [item[1] for item in linea]

        # Accesos por disciplina
        disc_rows = cur.execute(
            """
            SELECT disciplina, COUNT(*) as cnt
            FROM logs
            WHERE tipo='ACCESO' AND resultado='EXITO'
            AND disciplina IS NOT NULL AND disciplina != ''
            AND fecha >= ? || ' 00:00:00'
            GROUP BY disciplina
            ORDER BY cnt DESC
        """,
            (mes_inicio,)
        ).fetchall()
        disc_labels = [r[0] for r in disc_rows]
        disc_data = [r[1] for r in disc_rows]

    meses_es = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    return {
        "stats": {
            "total_clientes": total_clientes,
            "accesos_hoy": accesos_hoy,
            "accesos_mes": accesos_mes,
            "denegados_mes": denegados_mes,
            "clientes_vencidos": clientes_vencidos,
            "hora_pico": hora_pico,
            "fecha_hoy": hoy.strftime("%d/%m/%Y"),
            "mes_actual": meses_es[hoy.month],
        },
        "datos": {
            "dias_semana_labels": dias_semana_labels,
            "dias_semana_data": dias_semana_data,
            "horas_labels": horas_labels,
            "horas_data": horas_data,
            "top_clientes_nombres": top_clientes_nombres,
            "top_clientes_counts": top_clientes_counts,
            "resultados_labels": resultados_labels,
            "resultados_data": resultados_data,
            "linea_labels": linea_labels,
            "linea_data": linea_data,
            "disciplina_labels": disc_labels,
            "disciplina_data": disc_data,
        },
    }