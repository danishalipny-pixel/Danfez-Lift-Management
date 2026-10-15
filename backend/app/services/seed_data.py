from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.user import User
from ..models.building import Building
from ..models.elevator import Elevator
from ..models.technician import Technician
from ..models.maintenance import MaintenanceTicket
from ..models.fault import FaultAlert
from ..models.setting import SystemSetting
from ..auth.security import hash_password

def seed_database(db: Session):
    """Seed initial demonstration data for DANFEZ TECH HOUSE."""
    # 1. Users
    existing_admin = db.query(User).filter(User.email == "admin@danfez.com").first()
    if not existing_admin:
        admin_user = User(
            email="admin@danfez.com",
            hashed_password=hash_password("DanfezAdmin2026!"),
            full_name="Danfez Chief Administrator",
            role="admin",
            phone="+1 (555) 010-0100",
            is_active=True,
            is_verified=True
        )
        tech_user = User(
            email="tech@danfez.com",
            hashed_password=hash_password("DanfezTech2026!"),
            full_name="Marcus Vance (Field Engineer)",
            role="technician",
            phone="+1 (555) 010-0200",
            is_active=True,
            is_verified=True
        )
        viewer_user = User(
            email="viewer@danfez.com",
            hashed_password=hash_password("DanfezView2026!"),
            full_name="Building Inspector Guest",
            role="viewer",
            phone="+1 (555) 010-0300",
            is_active=True,
            is_verified=True
        )
        db.add_all([admin_user, tech_user, viewer_user])
        db.commit()
        db.refresh(admin_user)
        db.refresh(tech_user)

    # 2. Buildings
    if db.query(Building).count() == 0:
        hq_building = Building(
            name="Danfez HQ Tower",
            address="452 Silicon Boulevard, Tech District",
            total_floors=10
        )
        hub_building = Building(
            name="Danfez Innovation Hub",
            address="12 Industrial Innovation Way",
            total_floors=8
        )
        db.add_all([hq_building, hub_building])
        db.commit()
        db.refresh(hq_building)
        db.refresh(hub_building)

        # 3. Elevators
        lift_a1 = Elevator(
            name="Main Tower Passenger Lift A1",
            code="LIFT-A1",
            building_id=hq_building.id,
            floor_count=10,
            current_floor=1,
            target_floor=1,
            status="operational",
            direction="idle",
            door_state="closed",
            speed_multiplier=1.0,
            emergency_stopped=False,
            last_maintenance_date=datetime.utcnow() - timedelta(days=12)
        )
        lift_a2 = Elevator(
            name="Executive Express Lift A2",
            code="LIFT-A2",
            building_id=hq_building.id,
            floor_count=10,
            current_floor=4,
            target_floor=4,
            status="operational",
            direction="idle",
            door_state="closed",
            speed_multiplier=1.0,
            emergency_stopped=False,
            last_maintenance_date=datetime.utcnow() - timedelta(days=25)
        )
        lift_b1 = Elevator(
            name="Service Freight Lift B1",
            code="LIFT-B1",
            building_id=hub_building.id,
            floor_count=8,
            current_floor=2,
            target_floor=2,
            status="maintenance",
            direction="idle",
            door_state="closed",
            speed_multiplier=1.0,
            emergency_stopped=False,
            last_maintenance_date=datetime.utcnow() - timedelta(days=3)
        )
        db.add_all([lift_a1, lift_a2, lift_b1])
        db.commit()
        db.refresh(lift_a1)
        db.refresh(lift_a2)
        db.refresh(lift_b1)

        # 4. Technicians
        tech_user_record = db.query(User).filter(User.email == "tech@danfez.com").first()
        t1 = Technician(
            user_id=tech_user_record.id if tech_user_record else None,
            full_name="Marcus Vance",
            email="tech@danfez.com",
            phone="+1 (555) 010-0200",
            skills="Traction Motors, VFD Drive Systems, Safety Gear, Microprocessor Controllers",
            certification_level="Level 3 Master Specialist",
            status="Active",
            notes="Senior field engineer in charge of Danfez HQ Tower vertical transport systems."
        )
        t2 = Technician(
            full_name="Elena Rostova",
            email="elena.rostova@danfez.com",
            phone="+1 (555) 019-2841",
            skills="Door Operators, Infrared 3D Curtains, Interlocks, Load Weighers",
            certification_level="Level 2 Certified Elevator Technician",
            status="Active",
            notes="Certified sensor calibration and door mechanic."
        )
        t3 = Technician(
            full_name="Devon Chen",
            email="devon.chen@danfez.com",
            phone="+1 (555) 019-3321",
            skills="Hydraulic Pumps, Governor Inspection, Lubrication, Cable Tensioning",
            certification_level="Level 2 Certified Elevator Technician",
            status="Active",
            notes="Specialist in preventive maintenance and hydraulic elevators."
        )
        db.add_all([t1, t2, t3])
        db.commit()
        db.refresh(t1)
        db.refresh(t2)
        db.refresh(t3)

        # 5. Maintenance Tickets
        admin_rec = db.query(User).filter(User.email == "admin@danfez.com").first()
        admin_id = admin_rec.id if admin_rec else None

        tickets = [
            MaintenanceTicket(
                ticket_number="MNT-2026-001",
                elevator_id=lift_a1.id,
                category="Preventive Maintenance",
                priority="Medium",
                status="In Progress",
                description="Routine 30-day lubrication of guide rails, counterweight sheaves, and door track inspection.",
                assigned_technician_id=t1.id,
                created_by_id=admin_id,
                scheduled_date=datetime.utcnow() + timedelta(days=1),
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            MaintenanceTicket(
                ticket_number="MNT-2026-002",
                elevator_id=lift_a2.id,
                category="Door Sensor",
                priority="High",
                status="Resolved",
                description="Floor 4 optical safety edge curtain realignment and optical receiver lens cleaning.",
                assigned_technician_id=t2.id,
                created_by_id=admin_id,
                scheduled_date=datetime.utcnow() - timedelta(days=1),
                completion_date=datetime.utcnow() - timedelta(hours=4),
                resolution_notes="Cleaned optical sensor arrays and recalibrated sensitivity threshold. Tested 20 door cycles successfully.",
                created_at=datetime.utcnow() - timedelta(days=3)
            ),
            MaintenanceTicket(
                ticket_number="MNT-2026-003",
                elevator_id=lift_b1.id,
                category="Inspection",
                priority="Critical",
                status="In Progress",
                description="Annual mandatory safety gear overspeed governor mechanical trip verification and brake pad measurement.",
                assigned_technician_id=t3.id,
                created_by_id=admin_id,
                scheduled_date=datetime.utcnow(),
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            MaintenanceTicket(
                ticket_number="MNT-2026-004",
                elevator_id=lift_a1.id,
                category="Electrical",
                priority="Low",
                status="Closed",
                description="Replace LED floor indicator fixture on Cabin panel and update firmware to v2.4.",
                assigned_technician_id=t1.id,
                created_by_id=admin_id,
                scheduled_date=datetime.utcnow() - timedelta(days=7),
                completion_date=datetime.utcnow() - timedelta(days=6),
                resolution_notes="Replaced LED board and verified segment display output across all 10 floor stops.",
                created_at=datetime.utcnow() - timedelta(days=8)
            ),
            MaintenanceTicket(
                ticket_number="MNT-2026-005",
                elevator_id=lift_a2.id,
                category="Cable/Motor",
                priority="High",
                status="Assigned",
                description="Traction wire rope groove alignment inspection and tension balancing.",
                assigned_technician_id=t1.id,
                created_by_id=admin_id,
                scheduled_date=datetime.utcnow() + timedelta(days=4),
                created_at=datetime.utcnow() - timedelta(hours=8)
            )
        ]
        db.add_all(tickets)

        # 6. Fault Alerts
        faults = [
            FaultAlert(
                fault_code="FLT-2026-101",
                elevator_id=lift_a1.id,
                severity="Medium",
                category="Door Sensor",
                description="Simulated optical doorway curtain interrupted longer than 15 seconds without passenger clear signal.",
                is_acknowledged=True,
                acknowledged_at=datetime.utcnow() - timedelta(hours=5),
                acknowledged_by_id=admin_id,
                assigned_technician_id=t2.id,
                is_resolved=True,
                resolution_notes="Cleared obstruction test debris. Door safety loop returned to normal operational resistance.",
                resolved_at=datetime.utcnow() - timedelta(hours=3),
                resolved_by_id=admin_id,
                created_at=datetime.utcnow() - timedelta(hours=6)
            ),
            FaultAlert(
                fault_code="FLT-2026-102",
                elevator_id=lift_a2.id,
                severity="High",
                category="Motor Drive",
                description="Variable frequency drive heat sink thermal warning: temperature exceeded 65C during peak morning dispatch.",
                is_acknowledged=True,
                acknowledged_at=datetime.utcnow() - timedelta(hours=1),
                acknowledged_by_id=admin_id,
                assigned_technician_id=t1.id,
                is_resolved=False,
                created_at=datetime.utcnow() - timedelta(hours=2)
            ),
            FaultAlert(
                fault_code="FLT-2026-103",
                elevator_id=lift_a1.id,
                severity="Low",
                category="Controller Logic",
                description="Hall call station Floor 7 Up button momentary switch latency higher than normal nominal response.",
                is_acknowledged=False,
                is_resolved=False,
                created_at=datetime.utcnow() - timedelta(minutes=45)
            ),
            FaultAlert(
                fault_code="FLT-2026-104",
                elevator_id=lift_b1.id,
                severity="Critical",
                category="Safety Circuit",
                description="Safety circuit bypass loop voltage drop detected on Freight hoistway landing door lock circuit. Elevator placed into Maintenance Lockout.",
                is_acknowledged=True,
                acknowledged_at=datetime.utcnow() - timedelta(minutes=20),
                acknowledged_by_id=admin_id,
                assigned_technician_id=t3.id,
                is_resolved=False,
                created_at=datetime.utcnow() - timedelta(minutes=30)
            )
        ]
        db.add_all(faults)

        # 7. System Settings
        settings_data = [
            ("building_name", "Danfez HQ Tower", "Primary facility building name"),
            ("default_floors", "10", "Default floor count for newly created virtual lifts"),
            ("simulation_speed", "1.0", "Elevator simulation tick multiplier (1.0x, 2.0x, 5.0x)"),
            ("emergency_phone", "+1 (800) 555-DANFEZ", "24/7 Elevator Emergency Dispatch Line"),
            ("maintenance_interval_days", "30", "Mandatory preventive maintenance inspection interval"),
            ("email_notifications_enabled", "true", "Send email notifications for Critical and High severity faults"),
            ("theme_mode", "light_with_navy_sidebar", "Default system visual theme style")
        ]
        for key, val, desc in settings_data:
            db.add(SystemSetting(key=key, value=val, description=desc))

        db.commit()
