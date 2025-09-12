#!/usr/bin/env python3
"""
Sample input for epic_agent_enhanced.py
This file provides example POC details that you can use to test the epic generation system.
"""

# Sample POC 1: E-commerce Platform
POC_1 = {
    "title": "Smart E-commerce Platform with AI Recommendations",
    "description": "A modern e-commerce platform that uses AI to provide personalized product recommendations, dynamic pricing, and intelligent inventory management. The platform will serve both B2C and B2B customers with different user experiences.",
    "features": "AI product recommendations, dynamic pricing engine, inventory management, multi-vendor marketplace, mobile app, analytics dashboard, payment integration, order tracking, customer reviews, wishlist functionality",
    "tech_stack": "React.js, Node.js, Express, MongoDB, Redis, TensorFlow, Stripe API, AWS S3, Docker, Kubernetes",
    "target_users": "Online shoppers, store owners, marketplace vendors, platform administrators, marketing team, customer support",
    "business_goals": "Increase sales conversion by 25%, reduce cart abandonment by 30%, improve customer satisfaction scores, expand to new markets, reduce operational costs by 20%"
}

# Sample POC 2: Healthcare Management System
POC_2 = {
    "title": "Integrated Healthcare Management System",
    "description": "A comprehensive healthcare management system that connects patients, doctors, and healthcare facilities. Includes telemedicine capabilities, electronic health records, appointment scheduling, and prescription management with compliance to HIPAA regulations.",
    "features": "Patient portal, doctor dashboard, appointment scheduling, telemedicine video calls, electronic health records, prescription management, billing system, insurance verification, lab results integration, mobile app",
    "tech_stack": "Angular, Spring Boot, PostgreSQL, WebRTC, JWT authentication, AWS, Docker, Redis, Elasticsearch, HL7 FHIR",
    "target_users": "Patients, doctors, nurses, healthcare administrators, billing staff, insurance providers, lab technicians",
    "business_goals": "Improve patient care quality, reduce administrative overhead by 40%, increase patient satisfaction, ensure HIPAA compliance, streamline billing processes, reduce no-show rates by 50%"
}

# Sample POC 3: Smart City IoT Platform
POC_3 = {
    "title": "Smart City IoT Management Platform",
    "description": "An IoT platform for smart city management that monitors and controls various city infrastructure including traffic lights, waste management, air quality sensors, and public transportation. Includes real-time analytics and citizen engagement features.",
    "features": "IoT device management, real-time monitoring dashboard, traffic optimization, waste management tracking, air quality monitoring, citizen mobile app, emergency alert system, data analytics, predictive maintenance",
    "tech_stack": "React.js, Python Flask, InfluxDB, MQTT, Apache Kafka, Grafana, Docker, Kubernetes, AWS IoT Core, Machine Learning models",
    "target_users": "City administrators, traffic management staff, environmental monitoring team, citizens, emergency services, maintenance crews, data analysts",
    "business_goals": "Reduce traffic congestion by 20%, improve air quality monitoring, increase citizen engagement, optimize resource usage, reduce maintenance costs by 30%, enhance emergency response times"
}

# Sample POC 4: Learning Management System
POC_4 = {
    "title": "AI-Powered Learning Management System",
    "description": "A modern LMS with AI-driven personalized learning paths, automated assessment, and virtual classroom capabilities. Supports multiple learning formats including video, interactive content, and gamification elements.",
    "features": "Personalized learning paths, virtual classrooms, automated assessments, content creation tools, progress tracking, gamification, mobile learning, video conferencing, discussion forums, certificate generation",
    "tech_stack": "Vue.js, Django, PostgreSQL, WebRTC, TensorFlow, AWS S3, Redis, Celery, Docker, Nginx",
    "target_users": "Students, teachers, course creators, administrators, parents, corporate trainers, educational institutions",
    "business_goals": "Increase student engagement by 35%, improve learning outcomes, reduce administrative workload, expand to corporate training market, achieve 90% user satisfaction rating"
}

def get_sample_poc(poc_number=1):
    """Get a sample POC by number (1-4)"""
    pocs = {
        1: POC_1,
        2: POC_2,
        3: POC_3,
        4: POC_4
    }
    return pocs.get(poc_number, POC_1)

def format_poc_for_input(poc_data):
    """Format POC data for direct input into the epic generation system"""
    return f"""
POC Title: {poc_data['title']}
Description: {poc_data['description']}
Features: {poc_data['features']}
Tech Stack: {poc_data['tech_stack']}
Target Users: {poc_data['target_users']}
Business Goals: {poc_data['business_goals']}
"""

if __name__ == "__main__":
    print("Sample POC Data for Epic Generation System")
    print("=" * 50)
    
    for i in range(1, 5):
        poc = get_sample_poc(i)
        print(f"\nPOC {i}: {poc['title']}")
        print("-" * 30)
        print(format_poc_for_input(poc))
        print("\n" + "="*50)
