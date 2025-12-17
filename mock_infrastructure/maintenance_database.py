"""
Maintenance Records Database
SQLite database for storing and querying service logs
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class MaintenanceDatabase:
    """SQLite database for maintenance records"""
    
    def __init__(self, db_path: str = "mock_infrastructure/maintenance_records.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def initialize_schema(self):
        """Create database schema"""
        self.connect()
        
        # Vehicles table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                vin TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                manufacturing_batch TEXT,
                current_mileage INTEGER,
                owner_name TEXT,
                owner_email TEXT,
                owner_phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Service records table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vin TEXT NOT NULL,
                service_date TIMESTAMP NOT NULL,
                mileage INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                service_center TEXT,
                technician TEXT,
                cost REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vin) REFERENCES vehicles(vin)
            )
        ''')
        
        # Services performed table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services_performed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_record_id INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                FOREIGN KEY (service_record_id) REFERENCES service_records(id)
            )
        ''')
        
        # Parts replaced table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts_replaced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_record_id INTEGER NOT NULL,
                part_name TEXT NOT NULL,
                part_number TEXT,
                quantity INTEGER DEFAULT 1,
                cost REAL,
                FOREIGN KEY (service_record_id) REFERENCES service_records(id)
            )
        ''')
        
        # Create indexes
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_vin ON service_records(vin)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_date ON service_records(service_date)')
        
        self.conn.commit()
        print("Database schema initialized")
    
    def import_synthetic_data(self, vehicles_file: str = "mock_infrastructure/synthetic_vehicles.json"):
        """Import data from synthetic vehicles JSON"""
        with open(vehicles_file, 'r') as f:
            vehicles = json.load(f)
        
        for vehicle in vehicles:
            # Insert vehicle
            self.cursor.execute('''
                INSERT OR REPLACE INTO vehicles 
                (vin, model, year, manufacturing_batch, current_mileage, owner_name, owner_email, owner_phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vehicle["vin"],
                vehicle["model"],
                vehicle["year"],
                vehicle["manufacturing_batch"],
                vehicle["current_mileage"],
                vehicle["owner"]["name"],
                vehicle["owner"]["email"],
                vehicle["owner"]["phone"]
            ))
            
            # Insert maintenance history
            for record in vehicle.get("maintenance_history", []):
                self.cursor.execute('''
                    INSERT INTO service_records 
                    (vin, service_date, mileage, service_type, service_center, technician, cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vehicle["vin"],
                    record["date"],
                    record["mileage"],
                    record["service_type"],
                    record["service_center"],
                    record["technician"],
                    record["cost"]
                ))
                
                service_record_id = self.cursor.lastrowid
                
                # Insert services performed
                for service in record.get("services_performed", []):
                    self.cursor.execute('''
                        INSERT INTO services_performed (service_record_id, service_name)
                        VALUES (?, ?)
                    ''', (service_record_id, service))
                
                # Insert parts replaced
                for part in record.get("parts_replaced", []):
                    self.cursor.execute('''
                        INSERT INTO parts_replaced (service_record_id, part_name)
                        VALUES (?, ?)
                    ''', (service_record_id, part))
        
        self.conn.commit()
        print(f"Imported {len(vehicles)} vehicles with maintenance history")
    
    def get_vehicle(self, vin: str) -> Optional[Dict[str, Any]]:
        """Get vehicle by VIN"""
        self.cursor.execute('SELECT * FROM vehicles WHERE vin = ?', (vin,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Get all vehicles"""
        self.cursor.execute('SELECT * FROM vehicles')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_service_history(self, vin: str) -> List[Dict[str, Any]]:
        """Get service history for a vehicle"""
        self.cursor.execute('''
            SELECT * FROM service_records 
            WHERE vin = ? 
            ORDER BY service_date DESC
        ''', (vin,))
        
        records = []
        for row in self.cursor.fetchall():
            record = dict(row)
            
            # Get services performed
            self.cursor.execute('''
                SELECT service_name FROM services_performed 
                WHERE service_record_id = ?
            ''', (record['id'],))
            record['services_performed'] = [r['service_name'] for r in self.cursor.fetchall()]
            
            # Get parts replaced
            self.cursor.execute('''
                SELECT part_name, part_number, quantity, cost 
                FROM parts_replaced 
                WHERE service_record_id = ?
            ''', (record['id'],))
            record['parts_replaced'] = [dict(r) for r in self.cursor.fetchall()]
            
            records.append(record)
        
        return records
    
    def add_service_record(
        self,
        vin: str,
        service_date: str,
        mileage: int,
        service_type: str,
        services_performed: List[str],
        parts_replaced: List[Dict[str, Any]],
        service_center: str = None,
        technician: str = None,
        cost: float = None,
        notes: str = None
    ) -> int:
        """Add a new service record"""
        self.cursor.execute('''
            INSERT INTO service_records 
            (vin, service_date, mileage, service_type, service_center, technician, cost, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vin, service_date, mileage, service_type, service_center, technician, cost, notes))
        
        service_record_id = self.cursor.lastrowid
        
        # Add services performed
        for service in services_performed:
            self.cursor.execute('''
                INSERT INTO services_performed (service_record_id, service_name)
                VALUES (?, ?)
            ''', (service_record_id, service))
        
        # Add parts replaced
        for part in parts_replaced:
            self.cursor.execute('''
                INSERT INTO parts_replaced 
                (service_record_id, part_name, part_number, quantity, cost)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                service_record_id,
                part.get('name'),
                part.get('number'),
                part.get('quantity', 1),
                part.get('cost')
            ))
        
        self.conn.commit()
        return service_record_id
    
    def get_recent_services(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent service records"""
        self.cursor.execute('''
            SELECT sr.*, v.model, v.year, v.owner_name
            FROM service_records sr
            JOIN vehicles v ON sr.vin = v.vin
            WHERE sr.service_date >= datetime('now', '-' || ? || ' days')
            ORDER BY sr.service_date DESC
        ''', (days,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_vehicles_needing_service(self, mileage_threshold: int = 5000) -> List[Dict[str, Any]]:
        """Get vehicles that may need service soon"""
        self.cursor.execute('''
            SELECT v.*, 
                   MAX(sr.mileage) as last_service_mileage,
                   v.current_mileage - MAX(sr.mileage) as miles_since_service
            FROM vehicles v
            LEFT JOIN service_records sr ON v.vin = sr.vin
            GROUP BY v.vin
            HAVING miles_since_service >= ? OR miles_since_service IS NULL
        ''', (mileage_threshold,))
        
        return [dict(row) for row in self.cursor.fetchall()]


def initialize_database():
    """Initialize and populate database"""
    print("="*80)
    print("INITIALIZING MAINTENANCE RECORDS DATABASE")
    print("="*80)
    
    db = MaintenanceDatabase()
    db.initialize_schema()
    db.import_synthetic_data()
    
    # Show summary
    vehicles = db.get_all_vehicles()
    print(f"\nDatabase Summary:")
    print(f"  Total Vehicles: {len(vehicles)}")
    
    for vehicle in vehicles[:3]:
        history = db.get_service_history(vehicle['vin'])
        print(f"\n  {vehicle['vin']} ({vehicle['year']} {vehicle['model']})")
        print(f"    Owner: {vehicle['owner_name']}")
        print(f"    Mileage: {vehicle['current_mileage']:,}")
        print(f"    Service Records: {len(history)}")
    
    db.close()
    print("\n✓ Database initialized successfully")


if __name__ == "__main__":
    initialize_database()
