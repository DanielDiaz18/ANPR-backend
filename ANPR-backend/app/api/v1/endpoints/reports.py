from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_, func
from app.core.database import get_db
from app.models.vehicle import Vehicle
from app.models.client import Client
from app.models.service import Service
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import io
import matplotlib.pyplot as plt
import matplotlib
from collections import Counter
from datetime import date, datetime

# Use non-interactive backend
matplotlib.use('Agg')

router = APIRouter()

def get_filtered_data(
    db: Session,
    report_type: str,
    start_hour: int,
    end_hour: int,
    report_date: date | None = None,
    client_id: int | None = None,
    vehicle_id: int | None = None
):
    data = []
    
    if report_type == "client_vehicle_services":
        # This logic is complex because it combines multiple entities
        # For preview, we might just show services if that's the main focus, 
        # or a summary. Let's focus on services for the list.
        
        query = db.query(Service)
        
        # Date and Time filtering
        if report_date:
            query = query.filter(func.date(Service.created_at) == report_date)
        
        query = query.filter(
            extract('hour', Service.created_at) >= start_hour,
            extract('hour', Service.created_at) <= end_hour
        )
        
        if vehicle_id:
            query = query.filter(Service.vehicle_id == vehicle_id)
        elif client_id:
             # Find vehicles owned by client
             vehicles = db.query(Vehicle).filter(Vehicle.owner_id == client_id).all()
             vehicle_ids = [v.id for v in vehicles]
             query = query.filter(Service.vehicle_id.in_(vehicle_ids))
             
        services = query.all()
        
        for service in services:
            vehicle = service.vehicle
            client_name = "N/A"
            if vehicle and vehicle.owner:
                client_name = vehicle.owner.name
                
            data.append({
                "id": service.id,
                "col1": service.kind.value.replace("_", " ").title(), # Service Type
                "col2": vehicle.plate_id if vehicle else "N/A", # Plate
                "col3": client_name, # Client
                "created_at": service.created_at.strftime("%Y-%m-%d %H:%M")
            })
            
    elif report_type == "vehicles":
        query = db.query(Vehicle)
        
        if report_date:
            query = query.filter(func.date(Vehicle.created_at) == report_date)
            
        query = query.filter(
            extract('hour', Vehicle.created_at) >= start_hour,
            extract('hour', Vehicle.created_at) <= end_hour
        )
        
        if vehicle_id:
            query = query.filter(Vehicle.id == vehicle_id)
            
        vehicles = query.all()
        
        for vehicle in vehicles:
            data.append({
                "id": vehicle.id,
                "col1": vehicle.plate_id,
                "col2": vehicle.brand or "N/A",
                "col3": vehicle.model or "N/A",
                "created_at": vehicle.created_at.strftime("%Y-%m-%d %H:%M")
            })

    elif report_type == "clients":
        query = db.query(Client)
        
        if report_date:
            query = query.filter(func.date(Client.created_at) == report_date)
            
        query = query.filter(
            extract('hour', Client.created_at) >= start_hour,
            extract('hour', Client.created_at) <= end_hour
        )
        
        if client_id:
            query = query.filter(Client.id == client_id)
            
        clients = query.all()
        
        for client in clients:
            data.append({
                "id": client.id,
                "col1": client.name,
                "col2": client.email or "N/A",
                "col3": client.phone or "N/A",
                "created_at": client.created_at.strftime("%Y-%m-%d %H:%M")
            })
            
    return data

@router.get("/preview")
def get_report_preview(
    report_type: str, 
    start_hour: int = Query(0, ge=0, le=23),
    end_hour: int = Query(23, ge=0, le=23),
    report_date: date | None = Query(None),
    client_id: int = Query(None),
    vehicle_id: int = Query(None),
    db: Session = Depends(get_db)
):
    if start_hour > end_hour:
        raise HTTPException(status_code=400, detail="Start hour must be less than or equal to end hour.")
        
    data = get_filtered_data(db, report_type, start_hour, end_hour, report_date, client_id, vehicle_id)
    return {"data": data}

@router.get("/pdf")
def generate_pdf_report(
    report_type: str, 
    start_hour: int = Query(0, ge=0, le=23),
    end_hour: int = Query(23, ge=0, le=23),
    report_date: date | None = Query(None),
    client_id: int = Query(None),
    vehicle_id: int = Query(None),
    db: Session = Depends(get_db)
):
    if start_hour > end_hour:
        raise HTTPException(status_code=400, detail="Start hour must be less than or equal to end hour.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = f"{report_type.capitalize()} Report"
    elements.append(Paragraph(title, styles['Title']))
    
    time_range_str = f"Time Range: {start_hour}:00 - {end_hour}:59"
    if report_date:
        time_range_str += f" on {report_date.strftime('%Y-%m-%d')}"
    elements.append(Paragraph(time_range_str, styles['Normal']))
    
    if client_id:
        elements.append(Paragraph(f"Filtered by Client ID: {client_id}", styles['Normal']))
    if vehicle_id:
        elements.append(Paragraph(f"Filtered by Vehicle ID: {vehicle_id}", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = []
    hours = []
    
    # Re-using logic similar to preview but formatted for PDF
    # Note: The original PDF generation logic was quite specific with tables and charts.
    # I will adapt it to respect the date filter.
    
    if report_type == "client_vehicle_services":
        # ... (Existing logic adapted for date filtering) ...
        # For simplicity in this refactor, I'll stick to the core logic but apply the date filter to queries
        
        client = None
        vehicle = None
        
        if vehicle_id:
            vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            if vehicle and vehicle.owner_id:
                client = db.query(Client).filter(Client.id == vehicle.owner_id).first()
        
        if client_id and not client:
            client = db.query(Client).filter(Client.id == client_id).first()
            
        if not vehicle and not client:
             # If no specific client/vehicle selected, maybe we list all services in range?
             # The original code required client_id or vehicle_id. 
             # Let's relax this if we are doing a general report, OR keep it strict if that was intended.
             # The original code raised 400. Let's keep it consistent for single-entity reports,
             # BUT if we want a "general" report of all services in that hour, we should allow it.
             # Given the user wants to "see vehicles or clients", let's allow general listing if no ID provided.
             pass

        # If specific client/vehicle is selected, show their info
        if client:
            elements.append(Paragraph("Client Information", styles['Heading2']))
            client_data = [
                ["Field", "Value"],
                ["Name", client.name],
                ["Email", client.email or "N/A"],
                ["Phone", client.phone or "N/A"],
                ["Status", "Active" if client.enabled else "Inactive"],
                ["Registered", client.created_at.strftime("%Y-%m-%d %H:%M") if client.created_at else "N/A"]
            ]
            client_table = Table(client_data, colWidths=[150, 300])
            client_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(client_table)
            elements.append(Spacer(1, 12))
        
        if vehicle:
            elements.append(Paragraph("Vehicle Information", styles['Heading2']))
            vehicle_data = [
                ["Field", "Value"],
                ["Plate ID", vehicle.plate_id],
                ["Brand", vehicle.brand or "N/A"],
                ["Model", vehicle.model or "N/A"],
                ["Registered", vehicle.created_at.strftime("%Y-%m-%d %H:%M") if vehicle.created_at else "N/A"]
            ]
            vehicle_table = Table(vehicle_data, colWidths=[150, 300])
            vehicle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(vehicle_table)
            elements.append(Spacer(1, 12))

        # Services Section (General or Specific)
        elements.append(Paragraph("Services History", styles['Heading2']))
        services_query = db.query(Service)
        
        if vehicle:
            services_query = services_query.filter(Service.vehicle_id == vehicle.id)
        elif client:
             vehicles = db.query(Vehicle).filter(Vehicle.owner_id == client.id).all()
             vehicle_ids = [v.id for v in vehicles]
             services_query = services_query.filter(Service.vehicle_id.in_(vehicle_ids))

        # Apply time filter
        if report_date:
            services_query = services_query.filter(func.date(Service.created_at) == report_date)
            
        services_query = services_query.filter(
            extract('hour', Service.created_at) >= start_hour,
            extract('hour', Service.created_at) <= end_hour
        )
        
        services = services_query.all()
        
        if services:
            services_data = [["ID", "Service Type", "Vehicle", "Created At", "Status"]]
            for service in services:
                status = "Closed" if service.closed_at else "Open"
                service_type = service.kind.value.replace("_", " ").title()
                v_plate = service.vehicle.plate_id if service.vehicle else "N/A"
                services_data.append([
                    str(service.id),
                    service_type,
                    v_plate,
                    service.created_at.strftime("%Y-%m-%d %H:%M") if service.created_at else "N/A",
                    status
                ])
            
            services_table = Table(services_data)
            services_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(services_table)
            elements.append(Spacer(1, 12))
            
            # Service type distribution chart
            service_types = [s.kind.value for s in services]
            type_counts = Counter(service_types)
            
            if type_counts:
                plt.figure(figsize=(6, 4))
                types = [t.replace("_", " ").title() for t in type_counts.keys()]
                counts = list(type_counts.values())
                
                plt.bar(types, counts, color='skyblue')
                plt.xlabel('Service Type')
                plt.ylabel('Number of Services')
                plt.title('Services Distribution')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                plt.close()
                
                img = Image(img_buffer, width=400, height=300)
                elements.append(img)
        else:
            elements.append(Paragraph("No services found for the selected time range.", styles['Normal']))
        
    elif report_type == "vehicles":
        query = db.query(Vehicle)
        
        if report_date:
            query = query.filter(func.date(Vehicle.created_at) == report_date)
            
        query = query.filter(
            extract('hour', Vehicle.created_at) >= start_hour,
            extract('hour', Vehicle.created_at) <= end_hour
        )
        
        if vehicle_id:
            query = query.filter(Vehicle.id == vehicle_id)
            
        vehicles = query.all()
        
        # Table Header
        data.append(["ID", "Plate ID", "Brand", "Model", "Created At"])
        # Table Data
        for vehicle in vehicles:
            data.append([
                str(vehicle.id),
                vehicle.plate_id,
                vehicle.brand or "N/A",
                vehicle.model or "N/A",
                vehicle.created_at.strftime("%Y-%m-%d %H:%M") if vehicle.created_at else "N/A"
            ])
            if vehicle.created_at:
                hours.append(vehicle.created_at.hour)
            
    elif report_type == "clients":
        query = db.query(Client)
        
        if report_date:
            query = query.filter(func.date(Client.created_at) == report_date)
            
        query = query.filter(
            extract('hour', Client.created_at) >= start_hour,
            extract('hour', Client.created_at) <= end_hour
        )
        
        if client_id:
            query = query.filter(Client.id == client_id)
            
        clients = query.all()
        
        # Table Header
        data.append(["ID", "Name", "Email", "Phone", "Status"])
        # Table Data
        for client in clients:
            status = "Active" if client.enabled else "Inactive"
            data.append([
                str(client.id),
                client.name,
                client.email or "N/A",
                client.phone or "N/A",
                status
            ])
            if client.created_at:
                hours.append(client.created_at.hour)
    else:
        raise HTTPException(status_code=400, detail="Invalid report type. Must be 'vehicles', 'clients', or 'client_vehicle_services'.")

    # Generate Graph (Only for lists, not for single entity detailed reports usually, but let's keep it if we have hours data)
    if hours:
        plt.figure(figsize=(6, 4))
        hour_counts = Counter(hours)
        # Ensure all hours in range are represented
        all_hours = list(range(start_hour, end_hour + 1))
        counts = [hour_counts.get(h, 0) for h in all_hours]
        
        plt.bar(all_hours, counts, color='skyblue')
        plt.xlabel('Hour of Day')
        plt.ylabel('Number of Registrations')
        plt.title(f'Registrations by Hour ({start_hour}:00 - {end_hour}:59)')
        plt.xticks(all_hours)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close()
        
        img = Image(img_buffer, width=400, height=300)
        elements.append(img)
        elements.append(Spacer(1, 12))

    # Create Table (for lists)
    if len(data) > 1: # Header + at least one row
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
    elif report_type != "client_vehicle_services": # Don't show this if we already handled it in the special section
        elements.append(Paragraph("No data found for the selected time range.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    
    filename = f"{report_type}_report_{start_hour}-{end_hour}.pdf"
    return StreamingResponse(
        buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
