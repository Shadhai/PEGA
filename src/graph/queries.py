# ============================================================
# src/graph/queries.py
# ============================================================

import json
import os
from typing import Any, Dict, List

import kuzu


_GRAPH_INSTANCE = None


def get_graph():
    global _GRAPH_INSTANCE
    if _GRAPH_INSTANCE is None:
        _GRAPH_INSTANCE = ConstraintQueries()
    return _GRAPH_INSTANCE


class ConstraintQueries:
    def __init__(
        self,
        db_path: str = "data/graph_db.db",
        domain: str = "space",
    ):
        from pathlib import Path
        import shutil

        # KuzuDB 0.4+ expects a file path, not a directory.
        for p in [
            db_path,
            db_path + ".wal",
            db_path + ".lock",
            "data/graph_db_runtime",
            "data/graph_db",
        ]:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.domain = domain
        if domain == "industrial":
            self.joint_file = "data/extracted/joint_limits_industrial.json"
            self.obstacle_file = "data/extracted/obstacle_map_industrial.json"
            self.tool_file = "data/extracted/tool_catalog_industrial.json"
        else:
            self.joint_file = "data/extracted/joint_limits.json"
            self.obstacle_file = "data/extracted/obstacle_map.json"
            self.tool_file = "data/extracted/tool_catalog.json"


        self.db = kuzu.Database(
            db_path,
            buffer_pool_size=128 * 1024 * 1024,
            max_num_threads=2,
        )
        self.conn = kuzu.Connection(self.db)

        self._init_data()

    def _init_data(self):
        # --------------------------------------------------------
        # Remove existing tables so the database starts cleanly.
        # --------------------------------------------------------
        for table in ("Joint", "Obstacle", "Tool"):
            try:
                self.conn.execute(f"DROP TABLE {table}")
            except Exception:
                pass

        # --------------------------------------------------------
        # Node tables
        # --------------------------------------------------------

        self.conn.execute(
            """
            CREATE NODE TABLE Joint(
                name STRING,
                min_angle DOUBLE,
                max_angle DOUBLE,
                max_velocity DOUBLE,
                PRIMARY KEY(name)
            )
            """
        )

        self.conn.execute(
            """
            CREATE NODE TABLE Obstacle(
                name STRING,
                x DOUBLE,
                y DOUBLE,
                z DOUBLE,
                radius DOUBLE,
                clearance DOUBLE,
                PRIMARY KEY(name)
            )
            """
        )

        self.conn.execute(
            """
            CREATE NODE TABLE Tool(
                name STRING,
                max_force DOUBLE,
                weight DOUBLE,
                holster STRING,
                backup_holster STRING,
                PRIMARY KEY(name)
            )
            """
        )

        # --------------------------------------------------------
        # Load joints from:
        # data/extracted/joint_limits.json
        # --------------------------------------------------------

        joint_count = 0

        try:
            with open(
                self.joint_file,
                "r",
                encoding="utf-8",
            ) as f:
                joint_data = json.load(f)

            for j in joint_data.get("joints", []):
                name = str(j["joint"]).replace("'", "''")
                min_angle = float(j["min_deg"])
                max_angle = float(j["max_deg"])
                max_velocity = float(
                    j.get("max_vel_deg_s", 0.0)
                )

                self.conn.execute(
                    f"""
                    CREATE (:Joint {{
                        name: '{name}',
                        min_angle: {min_angle},
                        max_angle: {max_angle},
                        max_velocity: {max_velocity}
                    }})
                    """
                )

                joint_count += 1

        except Exception as e:
            print(f"  Joint load error: {e}")

        # --------------------------------------------------------
        # Load obstacles from:
        # data/extracted/obstacle_map.json
        # --------------------------------------------------------

        obstacle_count = 0

        try:
            with open(
                self.obstacle_file,
                "r",
                encoding="utf-8",
            ) as f:
                obstacle_data = json.load(f)

            for o in obstacle_data.get("obstacles", []):
                name = str(o["name"]).replace("'", "''")

                pos = o.get("pos_xyz", [0.0, 0.0, 0.0])
                size = o.get("size_m", [1.0, 1.0, 1.0])

                x = float(pos[0])
                y = float(pos[1])
                z = float(pos[2])

                # Approximate the obstacle as a sphere.
                # Radius = half of the largest dimension.
                radius = max(float(v) for v in size) / 2.0

                clearance = float(
                    o.get("clearance_m", 0.5)
                )

                self.conn.execute(
                    f"""
                    CREATE (:Obstacle {{
                        name: '{name}',
                        x: {x},
                        y: {y},
                        z: {z},
                        radius: {radius},
                        clearance: {clearance}
                    }})
                    """
                )

                obstacle_count += 1

        except Exception as e:
            print(f"  Obstacle load error: {e}")

        # --------------------------------------------------------
        # Load tools from:
        # data/extracted/tool_catalog.json
        # --------------------------------------------------------

        tool_count = 0

        try:
            with open(
                self.tool_file,
                "r",
                encoding="utf-8",
            ) as f:
                tool_data = json.load(f)

            for t in tool_data.get("tools", []):
                name = str(t["name"]).replace("'", "''")

                max_force = float(
                    t.get("max_force_n", 0.0)
                )

                weight = float(
                    t.get("mass_kg", 0.0)
                )

                # Prefer explicit holster IDs from the JSON.
                # Fall back to generated IDs if missing.
                holster = str(
                    t.get(
                        "holster_id",
                        f"H-{abs(hash(name)) % 9 + 1}",
                    )
                ).replace("'", "''")

                backup_holster = str(
                    t.get(
                        "backup_holster",
                        f"H-{abs(hash(name)) % 9 + 2}",
                    )
                ).replace("'", "''")

                self.conn.execute(
                    f"""
                    CREATE (:Tool {{
                        name: '{name}',
                        max_force: {max_force},
                        weight: {weight},
                        holster: '{holster}',
                        backup_holster: '{backup_holster}'
                    }})
                    """
                )

                tool_count += 1

        except Exception as e:
            print(f"  Tool load error: {e}")

        # --------------------------------------------------------
        # Summary
        # --------------------------------------------------------

        print(
            "  Graph DB ready with real NASA data: "
            f"{joint_count} joints, "
            f"{obstacle_count} obstacles, "
            f"{tool_count} tools"
        )


    def check_collision_trajectory(
        self,
        x: float,
        y: float,
        z: float,
        margin_scale: float = 0.4,
    ) -> Dict[str, Any]:
        """Collision check for intermediate trajectory waypoints."""
        try:
            result = self.conn.execute(
                "MATCH (o:Obstacle) "
                "RETURN o.name, o.x, o.y, o.z, o.radius, o.clearance"
            )
            while result.has_next():
                row = result.get_next()
                name, ox, oy, oz, radius, clearance = row
                distance = ((x - ox) ** 2 + (y - oy) ** 2 + (z - oz) ** 2) ** 0.5
                safe_distance = radius + clearance * margin_scale
                if distance < safe_distance:
                    return {
                        "passed": False,
                        "violation": (
                            f"Trajectory collision with {name} "
                            f"(dist: {distance:.2f}m, "
                            f"waypoint_need: {safe_distance:.2f}m)"
                        ),
                        "severity": 0.7,
                    }
            return {"passed": True, "violation": None, "severity": 0.0}
        except Exception as e:
            return {"passed": False, "violation": str(e), "severity": 0.5}

    def check_joint_limits(
        self,
        joint_name: str,
        angle: float,
    ) -> Dict[str, Any]:
        try:
            # Escape single quotes in the user-provided name.
            safe_joint_name = joint_name.replace("'", "''")

            result = self.conn.execute(
                f"""
                MATCH (j:Joint)
                WHERE j.name = '{safe_joint_name}'
                RETURN j.min_angle, j.max_angle
                """
            )

            if result.has_next():
                row = result.get_next()
                min_angle, max_angle = row[0], row[1]

                if angle < min_angle:
                    return {
                        "passed": False,
                        "violation": (
                            f"Angle {angle} below minimum "
                            f"{min_angle}"
                        ),
                        "severity": 1.0,
                    }

                if angle > max_angle:
                    return {
                        "passed": False,
                        "violation": (
                            f"Angle {angle} above maximum "
                            f"{max_angle}"
                        ),
                        "severity": 1.0,
                    }

                return {
                    "passed": True,
                    "violation": None,
                    "severity": 0.0,
                }

            return {
                "passed": False,
                "violation": f"Joint {joint_name} not found",
                "severity": 0.5,
            }

        except Exception as e:
            return {
                "passed": False,
                "violation": str(e),
                "severity": 0.5,
            }

    def check_collision(
        self,
        x: float,
        y: float,
        z: float,
    ) -> Dict[str, Any]:
        try:
            result = self.conn.execute(
                """
                MATCH (o:Obstacle)
                RETURN
                    o.name,
                    o.x,
                    o.y,
                    o.z,
                    o.radius,
                    o.clearance
                """
            )

            while result.has_next():
                row = result.get_next()

                name, ox, oy, oz, radius, clearance = row

                distance = (
                    (x - ox) ** 2
                    + (y - oy) ** 2
                    + (z - oz) ** 2
                ) ** 0.5

                safe_distance = radius + clearance

                if distance < safe_distance:
                    return {
                        "passed": False,
                        "violation": (
                            f"Collision with {name} "
                            f"(dist: {distance:.2f}m, "
                            f"need: {safe_distance:.2f}m)"
                        ),
                        "severity": 1.0,
                    }

            return {
                "passed": True,
                "violation": None,
                "severity": 0.0,
            }

        except Exception as e:
            return {
                "passed": False,
                "violation": str(e),
                "severity": 0.5,
            }

    def check_tool_force(
        self,
        tool_name: str,
        force: float,
    ) -> Dict[str, Any]:
        try:
            # Escape single quotes in the user-provided name.
            safe_tool_name = tool_name.replace("'", "''")

            result = self.conn.execute(
                f"""
                MATCH (t:Tool)
                WHERE t.name = '{safe_tool_name}'
                RETURN t.max_force
                """
            )

            if result.has_next():
                max_force = result.get_next()[0]

                if force > max_force:
                    return {
                        "passed": False,
                        "violation": (
                            f"Force {force}N exceeds max "
                            f"{max_force}N"
                        ),
                        "severity": 0.9,
                    }

                return {
                    "passed": True,
                    "violation": None,
                    "severity": 0.0,
                }

            return {
                "passed": False,
                "violation": f"Tool {tool_name} not found",
                "severity": 0.3,
            }

        except Exception as e:
            return {
                "passed": False,
                "violation": str(e),
                "severity": 0.5,
            }

    def get_all_constraints(
        self,
        command: str,
    ) -> List[Dict[str, Any]]:
        constraints: List[Dict[str, Any]] = []

        try:
            # ----------------------------------------------------
            # Joint constraints
            # ----------------------------------------------------

            result = self.conn.execute(
                """
                MATCH (j:Joint)
                RETURN
                    j.name,
                    j.min_angle,
                    j.max_angle
                """
            )

            while result.has_next():
                row = result.get_next()

                constraints.append(
                    {
                        "type": "joint",
                        "name": row[0],
                        "min": row[1],
                        "max": row[2],
                    }
                )

            # ----------------------------------------------------
            # Obstacle constraints
            # ----------------------------------------------------

            result = self.conn.execute(
                """
                MATCH (o:Obstacle)
                RETURN
                    o.name,
                    o.x,
                    o.y,
                    o.z,
                    o.clearance
                """
            )

            while result.has_next():
                row = result.get_next()

                constraints.append(
                    {
                        "type": "obstacle",
                        "name": row[0],
                        "pos": [
                            row[1],
                            row[2],
                            row[3],
                        ],
                        "clearance": row[4],
                    }
                )

            # ----------------------------------------------------
            # Tool constraints
            # ----------------------------------------------------

            result = self.conn.execute(
                """
                MATCH (t:Tool)
                RETURN
                    t.name,
                    t.max_force
                """
            )

            while result.has_next():
                row = result.get_next()

                constraints.append(
                    {
                        "type": "tool",
                        "name": row[0],
                        "max_force": row[1],
                    }
                )

        except Exception as e:
            print(f"  Graph query note: {e}")

        return constraints