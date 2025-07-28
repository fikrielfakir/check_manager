#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Analytics Engine for Cheque Management System
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ClientRiskProfile:
    client_id: int
    client_name: str
    risk_level: RiskLevel
    bounce_rate: float
    total_cheques: int
    total_amount: float
    avg_processing_time: float
    last_bounce_date: Optional[date]
    risk_score: float

@dataclass
class ChequeAgingData:
    status: str
    avg_days: float
    min_days: int
    max_days: int
    count: int
    percentage: float

class AdvancedAnalytics:
    """Advanced analytics engine for cheque management"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_cheque_aging_analysis(self, date_from: str = None, date_to: str = None) -> List[ChequeAgingData]:
        """
        Analyze how long cheques spend in each status
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                query = """
                WITH cheque_status_duration AS (
                    SELECT 
                        c.id,
                        c.status,
                        c.created_at,
                        c.updated_at,
                        CASE 
                            WHEN c.status = 'en_attente' THEN 
                                julianday('now') - julianday(c.created_at)
                            ELSE 
                                julianday(c.updated_at) - julianday(c.created_at)
                        END as days_in_status
                    FROM cheques c
                    WHERE 1=1
                """
                
                params = []
                if date_from:
                    query += " AND date(c.created_at) >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND date(c.created_at) <= ?"
                    params.append(date_to)
                
                query += """
                )
                SELECT 
                    status,
                    AVG(days_in_status) as avg_days,
                    MIN(days_in_status) as min_days,
                    MAX(days_in_status) as max_days,
                    COUNT(*) as count,
                    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM cheque_status_duration) as percentage
                FROM cheque_status_duration
                GROUP BY status
                ORDER BY avg_days DESC
                """
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [
                    ChequeAgingData(
                        status=row[0],
                        avg_days=round(row[1], 2),
                        min_days=int(row[2]),
                        max_days=int(row[3]),
                        count=row[4],
                        percentage=round(row[5], 2)
                    )
                    for row in results
                ]
                
        except Exception as e:
            self.logger.error(f"Error in cheque aging analysis: {e}")
            return []
    
    def get_seasonal_trends(self, years: int = 2) -> Dict:
        """
        Analyze seasonal trends in cheque inflow/outflow
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Monthly trends
                cursor.execute("""
                    SELECT 
                        strftime('%m', created_at) as month,
                        strftime('%Y', created_at) as year,
                        COUNT(*) as cheque_count,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_amount
                    FROM cheques 
                    WHERE created_at >= date('now', '-{} years')
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY year, month
                """.format(years))
                
                monthly_data = cursor.fetchall()
                
                # Quarterly trends
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN CAST(strftime('%m', created_at) AS INTEGER) <= 3 THEN 'Q1'
                            WHEN CAST(strftime('%m', created_at) AS INTEGER) <= 6 THEN 'Q2'
                            WHEN CAST(strftime('%m', created_at) AS INTEGER) <= 9 THEN 'Q3'
                            ELSE 'Q4'
                        END as quarter,
                        strftime('%Y', created_at) as year,
                        COUNT(*) as cheque_count,
                        SUM(amount) as total_amount
                    FROM cheques 
                    WHERE created_at >= date('now', '-{} years')
                    GROUP BY year, quarter
                    ORDER BY year, quarter
                """.format(years))
                
                quarterly_data = cursor.fetchall()
                
                # Day of week patterns
                cursor.execute("""
                    SELECT 
                        CASE strftime('%w', created_at)
                            WHEN '0' THEN 'Dimanche'
                            WHEN '1' THEN 'Lundi'
                            WHEN '2' THEN 'Mardi'
                            WHEN '3' THEN 'Mercredi'
                            WHEN '4' THEN 'Jeudi'
                            WHEN '5' THEN 'Vendredi'
                            WHEN '6' THEN 'Samedi'
                        END as day_of_week,
                        COUNT(*) as cheque_count,
                        AVG(amount) as avg_amount
                    FROM cheques 
                    WHERE created_at >= date('now', '-1 year')
                    GROUP BY strftime('%w', created_at)
                    ORDER BY strftime('%w', created_at)
                """)
                
                daily_patterns = cursor.fetchall()
                
                return {
                    'monthly_trends': monthly_data,
                    'quarterly_trends': quarterly_data,
                    'daily_patterns': daily_patterns
                }
                
        except Exception as e:
            self.logger.error(f"Error in seasonal trends analysis: {e}")
            return {}
    
    def calculate_client_risk_profiles(self) -> List[ClientRiskProfile]:
        """
        Calculate comprehensive risk profiles for all clients
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        cl.id,
                        cl.name,
                        COUNT(c.id) as total_cheques,
                        SUM(c.amount) as total_amount,
                        SUM(CASE WHEN c.status IN ('rejete', 'impaye') THEN 1 ELSE 0 END) as bounced_cheques,
                        AVG(julianday(c.updated_at) - julianday(c.created_at)) as avg_processing_time,
                        MAX(CASE WHEN c.status IN ('rejete', 'impaye') THEN c.updated_at END) as last_bounce_date,
                        AVG(c.amount) as avg_cheque_amount,
                        COUNT(DISTINCT strftime('%Y-%m', c.created_at)) as active_months
                    FROM clients cl
                    LEFT JOIN cheques c ON cl.id = c.client_id
                    WHERE cl.active = TRUE
                    GROUP BY cl.id, cl.name
                    HAVING total_cheques > 0
                    ORDER BY total_amount DESC
                """)
                
                results = cursor.fetchall()
                risk_profiles = []
                
                for row in results:
                    client_id, name, total_cheques, total_amount, bounced_cheques, avg_processing_time, last_bounce_date, avg_amount, active_months = row
                    
                    # Calculate bounce rate
                    bounce_rate = (bounced_cheques / total_cheques * 100) if total_cheques > 0 else 0
                    
                    # Calculate risk score (0-100, higher = riskier)
                    risk_score = self._calculate_risk_score(
                        bounce_rate, total_cheques, total_amount or 0, 
                        avg_processing_time or 0, last_bounce_date, active_months or 1
                    )
                    
                    # Determine risk level
                    if risk_score >= 80:
                        risk_level = RiskLevel.CRITICAL
                    elif risk_score >= 60:
                        risk_level = RiskLevel.HIGH
                    elif risk_score >= 40:
                        risk_level = RiskLevel.MEDIUM
                    else:
                        risk_level = RiskLevel.LOW
                    
                    risk_profiles.append(ClientRiskProfile(
                        client_id=client_id,
                        client_name=name,
                        risk_level=risk_level,
                        bounce_rate=round(bounce_rate, 2),
                        total_cheques=total_cheques,
                        total_amount=total_amount or 0,
                        avg_processing_time=round(avg_processing_time or 0, 2),
                        last_bounce_date=datetime.strptime(last_bounce_date, '%Y-%m-%d %H:%M:%S').date() if last_bounce_date else None,
                        risk_score=round(risk_score, 2)
                    ))
                
                return risk_profiles
                
        except Exception as e:
            self.logger.error(f"Error calculating client risk profiles: {e}")
            return []
    
    def _calculate_risk_score(self, bounce_rate: float, total_cheques: int, 
                            total_amount: float, avg_processing_time: float, 
                            last_bounce_date: str, active_months: int) -> float:
        """
        Calculate a comprehensive risk score for a client
        """
        score = 0
        
        # Bounce rate factor (0-40 points)
        score += min(bounce_rate * 2, 40)
        
        # Volume factor (0-20 points, inverse relationship)
        if total_cheques < 5:
            score += 20
        elif total_cheques < 20:
            score += 10
        
        # Amount factor (0-15 points, inverse relationship)
        if total_amount < 10000:
            score += 15
        elif total_amount < 50000:
            score += 8
        
        # Processing time factor (0-10 points)
        if avg_processing_time > 30:
            score += 10
        elif avg_processing_time > 14:
            score += 5
        
        # Recent bounce factor (0-15 points)
        if last_bounce_date:
            try:
                last_bounce = datetime.strptime(last_bounce_date, '%Y-%m-%d %H:%M:%S')
                days_since_bounce = (datetime.now() - last_bounce).days
                if days_since_bounce < 30:
                    score += 15
                elif days_since_bounce < 90:
                    score += 10
                elif days_since_bounce < 180:
                    score += 5
            except:
                pass
        
        return min(score, 100)
    
    def get_performance_metrics(self, date_from: str = None, date_to: str = None) -> Dict:
        """
        Calculate comprehensive performance metrics
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Base query conditions
                where_clause = "WHERE 1=1"
                params = []
                
                if date_from:
                    where_clause += " AND date(c.created_at) >= ?"
                    params.append(date_from)
                if date_to:
                    where_clause += " AND date(c.created_at) <= ?"
                    params.append(date_to)
                
                # Overall metrics
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_cheques,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_amount,
                        SUM(CASE WHEN status = 'encaisse' THEN 1 ELSE 0 END) as successful_cheques,
                        SUM(CASE WHEN status IN ('rejete', 'impaye') THEN 1 ELSE 0 END) as failed_cheques,
                        AVG(CASE WHEN status IN ('encaisse', 'rejete', 'impaye') 
                            THEN julianday(updated_at) - julianday(created_at) END) as avg_processing_time,
                        COUNT(DISTINCT client_id) as unique_clients,
                        COUNT(DISTINCT branch_id) as unique_branches
                    FROM cheques c {where_clause}
                """, params)
                
                overall_metrics = cursor.fetchone()
                
                # Success rate calculation
                total_processed = overall_metrics[3] + overall_metrics[4]  # successful + failed
                success_rate = (overall_metrics[3] / total_processed * 100) if total_processed > 0 else 0
                
                # Bank performance
                cursor.execute(f"""
                    SELECT 
                        bk.name as bank_name,
                        COUNT(c.id) as cheque_count,
                        SUM(c.amount) as total_amount,
                        AVG(CASE WHEN c.status IN ('encaisse', 'rejete', 'impaye') 
                            THEN julianday(c.updated_at) - julianday(c.created_at) END) as avg_processing_time,
                        SUM(CASE WHEN c.status = 'encaisse' THEN 1 ELSE 0 END) * 100.0 / 
                            NULLIF(SUM(CASE WHEN c.status IN ('encaisse', 'rejete', 'impaye') THEN 1 ELSE 0 END), 0) as success_rate
                    FROM cheques c
                    JOIN branches b ON c.branch_id = b.id
                    JOIN banks bk ON b.bank_id = bk.id
                    {where_clause}
                    GROUP BY bk.id, bk.name
                    ORDER BY total_amount DESC
                """, params)
                
                bank_performance = cursor.fetchall()
                
                # Monthly trends
                cursor.execute(f"""
                    SELECT 
                        strftime('%Y-%m', created_at) as month,
                        COUNT(*) as cheque_count,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_amount,
                        SUM(CASE WHEN status = 'encaisse' THEN 1 ELSE 0 END) * 100.0 / 
                            NULLIF(SUM(CASE WHEN status IN ('encaisse', 'rejete', 'impaye') THEN 1 ELSE 0 END), 0) as success_rate
                    FROM cheques c {where_clause}
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY month DESC
                    LIMIT 12
                """, params)
                
                monthly_trends = cursor.fetchall()
                
                return {
                    'overall': {
                        'total_cheques': overall_metrics[0],
                        'total_amount': overall_metrics[1] or 0,
                        'avg_amount': round(overall_metrics[2] or 0, 2),
                        'success_rate': round(success_rate, 2),
                        'avg_processing_time': round(overall_metrics[5] or 0, 2),
                        'unique_clients': overall_metrics[6],
                        'unique_branches': overall_metrics[7]
                    },
                    'bank_performance': bank_performance,
                    'monthly_trends': monthly_trends
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def predict_cash_flow(self, days_ahead: int = 30) -> Dict:
        """
        Predict future cash flow based on pending cheques and historical patterns
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get pending cheques
                cursor.execute("""
                    SELECT 
                        due_date,
                        SUM(amount) as total_amount,
                        COUNT(*) as cheque_count
                    FROM cheques 
                    WHERE status IN ('en_attente', 'depose')
                    AND due_date BETWEEN date('now') AND date('now', '+{} days')
                    GROUP BY due_date
                    ORDER BY due_date
                """.format(days_ahead))
                
                pending_cheques = cursor.fetchall()
                
                # Calculate success probability based on historical data
                cursor.execute("""
                    SELECT 
                        AVG(CASE WHEN status = 'encaisse' THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM cheques 
                    WHERE status IN ('encaisse', 'rejete', 'impaye')
                    AND created_at >= date('now', '-1 year')
                """)
                
                historical_success_rate = cursor.fetchone()[0] or 0.8
                
                # Generate predictions
                predictions = []
                cumulative_amount = 0
                
                for due_date, amount, count in pending_cheques:
                    expected_amount = amount * historical_success_rate
                    cumulative_amount += expected_amount
                    
                    predictions.append({
                        'date': due_date,
                        'expected_amount': round(expected_amount, 2),
                        'cheque_count': count,
                        'cumulative_amount': round(cumulative_amount, 2),
                        'confidence': round(historical_success_rate * 100, 1)
                    })
                
                return {
                    'predictions': predictions,
                    'summary': {
                        'total_expected': round(cumulative_amount, 2),
                        'total_pending': sum(row[1] for row in pending_cheques),
                        'success_rate': round(historical_success_rate * 100, 1),
                        'days_analyzed': days_ahead
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error predicting cash flow: {e}")
            return {}
    
    def get_duplicate_detection_analysis(self) -> List[Dict]:
        """
        Advanced duplicate detection with fuzzy matching
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        c1.id as id1,
                        c1.cheque_number as number1,
                        c1.amount as amount1,
                        c1.client_id as client1,
                        c1.created_at as date1,
                        c2.id as id2,
                        c2.cheque_number as number2,
                        c2.amount as amount2,
                        c2.client_id as client2,
                        c2.created_at as date2,
                        cl1.name as client_name1,
                        cl2.name as client_name2
                    FROM cheques c1
                    JOIN cheques c2 ON c1.id < c2.id
                    LEFT JOIN clients cl1 ON c1.client_id = cl1.id
                    LEFT JOIN clients cl2 ON c2.client_id = cl2.id
                    WHERE (
                        c1.cheque_number = c2.cheque_number OR
                        (c1.amount = c2.amount AND c1.client_id = c2.client_id AND 
                         abs(julianday(c1.created_at) - julianday(c2.created_at)) <= 7)
                    )
                    ORDER BY c1.created_at DESC
                """)
                
                potential_duplicates = []
                for row in cursor.fetchall():
                    similarity_score = self._calculate_similarity_score(row)
                    if similarity_score > 0.7:  # 70% similarity threshold
                        potential_duplicates.append({
                            'cheque1': {
                                'id': row[0],
                                'number': row[1],
                                'amount': row[2],
                                'client': row[10],
                                'date': row[4]
                            },
                            'cheque2': {
                                'id': row[5],
                                'number': row[6],
                                'amount': row[7],
                                'client': row[11],
                                'date': row[9]
                            },
                            'similarity_score': round(similarity_score * 100, 1),
                            'match_reasons': self._get_match_reasons(row)
                        })
                
                return potential_duplicates
                
        except Exception as e:
            self.logger.error(f"Error in duplicate detection: {e}")
            return []
    
    def _calculate_similarity_score(self, row) -> float:
        """Calculate similarity score between two cheques"""
        score = 0
        
        # Exact cheque number match
        if row[1] == row[6]:
            score += 0.5
        
        # Exact amount match
        if row[2] == row[7]:
            score += 0.3
        
        # Same client
        if row[3] == row[8]:
            score += 0.2
        
        # Date proximity (within 7 days)
        try:
            date1 = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
            date2 = datetime.strptime(row[9], '%Y-%m-%d %H:%M:%S')
            days_diff = abs((date1 - date2).days)
            if days_diff <= 1:
                score += 0.2
            elif days_diff <= 7:
                score += 0.1
        except:
            pass
        
        return min(score, 1.0)
    
    def _get_match_reasons(self, row) -> List[str]:
        """Get reasons why two cheques might be duplicates"""
        reasons = []
        
        if row[1] == row[6]:
            reasons.append("Même numéro de chèque")
        
        if row[2] == row[7]:
            reasons.append("Même montant")
        
        if row[3] == row[8]:
            reasons.append("Même client")
        
        try:
            date1 = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
            date2 = datetime.strptime(row[9], '%Y-%m-%d %H:%M:%S')
            days_diff = abs((date1 - date2).days)
            if days_diff <= 7:
                reasons.append(f"Dates proches ({days_diff} jour(s))")
        except:
            pass
        
        return reasons