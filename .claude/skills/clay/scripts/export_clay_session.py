#!/usr/bin/env python3
"""
Clay Session Data Exporter

Collects all Clay data from a session and exports to CSV files.
Usage: python export_clay_session.py <output_dir> [tool_results_dir]

This script should be run at the end of any Clay session to ensure
no data is lost. Clay credits are already spent—always collect everything.
"""

import json
import csv
import os
import sys
from datetime import datetime
from pathlib import Path


class ClaySessionCollector:
    """Collects and exports all Clay data from a session."""

    def __init__(self, context=""):
        self.companies = {}
        self.contacts = []
        self.jobs = []
        self.enrichments = []
        self.search_ids = []
        self.context = context  # User intent description
        self.date_added = datetime.now().strftime('%Y-%m-%d')

    def parse_tool_result_file(self, filepath):
        """Parse Clay data from tool results file (handles wrapped format)."""
        with open(filepath) as f:
            try:
                raw = json.load(f)
            except json.JSONDecodeError:
                return None

        # Unwrap if needed
        if isinstance(raw, list) and raw and isinstance(raw[0], dict) and 'text' in raw[0]:
            try:
                return json.loads(raw[0]['text'])
            except json.JSONDecodeError:
                return None
        elif isinstance(raw, dict) and 'text' in raw:
            try:
                return json.loads(raw['text'])
            except json.JSONDecodeError:
                return None
        return raw

    def add_search_result(self, data):
        """Add a Clay search result to the collector."""
        if not data or not isinstance(data, dict):
            return

        search_id = data.get('searchId')
        if search_id:
            self.search_ids.append(search_id)

        # Process companies
        for domain, company in data.get('companies', {}).items():
            if domain not in self.companies:
                self.companies[domain] = company
            else:
                # Merge enrichments
                existing = self.companies[domain]
                for eid, enrichment in company.get('enrichments', {}).items():
                    if 'enrichments' not in existing:
                        existing['enrichments'] = {}
                    existing['enrichments'][eid] = enrichment

            # Extract enrichments
            for eid, enrichment in company.get('enrichments', {}).items():
                self.enrichments.append({
                    'company_domain': domain,
                    'company_name': company.get('name', ''),
                    'enrichment_id': eid,
                    'type': enrichment.get('name'),
                    'state': enrichment.get('state'),
                    'value': self._truncate_value(enrichment.get('value')),
                    'provider': enrichment.get('metadata', {}).get('provider', 'unknown')
                               if isinstance(enrichment.get('metadata'), dict) else 'unknown'
                })

                # Extract jobs if Open Jobs enrichment
                if enrichment.get('name') == 'Open Jobs' and enrichment.get('value'):
                    self._extract_jobs(enrichment['value'], domain, company.get('name', ''))

        # Process contacts (dedupe by profile_id)
        for contact in data.get('contacts', []):
            if not any(c.get('profile_id') == contact.get('profile_id') for c in self.contacts):
                self.contacts.append(contact)

    def _extract_jobs(self, value, company_domain, company_name):
        """Extract job listings from Open Jobs enrichment."""
        try:
            jobs_data = json.loads(value) if isinstance(value, str) else value
            for job in jobs_data.get('jobs', []):
                job['source_company_domain'] = company_domain
                job['source_company_name'] = company_name
                self.jobs.append(job)
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    def _truncate_value(self, value, max_length=1000):
        """Truncate long values for CSV export."""
        if value is None:
            return ''
        if isinstance(value, dict):
            value = json.dumps(value)
        value = str(value)
        return value[:max_length] + '...' if len(value) > max_length else value

    def filter_current_employees(self, target_company, target_domain):
        """Filter contacts to only current employees."""
        return [
            c for c in self.contacts
            if (c.get('latest_experience_company', '').lower() == target_company.lower() or
                c.get('domain', '').lower() == target_domain.lower())
        ]

    def export_companies(self, output_path):
        """Export companies to CSV."""
        if not self.companies:
            return 0

        fieldnames = [
            'name', 'domain', 'linkedin_url', 'website', 'industry', 'type',
            'employee_count', 'size', 'country', 'locality', 'description',
            'annual_revenue', 'total_funding', 'logo_url',
            'headcount_growth_12mo', 'website_traffic', 'open_jobs_count',
            'context', 'date_added'
        ]

        rows = []
        for domain, company in self.companies.items():
            hg_12mo = None
            website_traffic = None
            open_jobs_count = 0

            for enrichment in company.get('enrichments', {}).values():
                name = enrichment.get('name', '')
                value = enrichment.get('value')

                if name == 'Headcount Growth' and value:
                    try:
                        hg_data = json.loads(value) if isinstance(value, str) else value
                        hg_12mo = hg_data.get('percent_employee_growth_over_last_12_months')
                    except:
                        pass
                elif name == 'Website Traffic':
                    website_traffic = value
                elif name == 'Open Jobs' and value:
                    try:
                        jobs_data = json.loads(value) if isinstance(value, str) else value
                        open_jobs_count = jobs_data.get('count', len(jobs_data.get('jobs', [])))
                    except:
                        pass

            rows.append({
                'name': company.get('name', ''),
                'domain': domain,
                'linkedin_url': company.get('url', ''),
                'website': company.get('website', ''),
                'industry': company.get('industry', ''),
                'type': company.get('type', ''),
                'employee_count': company.get('employee_count', ''),
                'size': company.get('size', ''),
                'country': company.get('country', ''),
                'locality': company.get('locality', ''),
                'description': (company.get('description', '') or '')[:500],
                'annual_revenue': company.get('annual_revenue', ''),
                'total_funding': company.get('total_funding_amount_range_usd', ''),
                'logo_url': company.get('logo_url', ''),
                'headcount_growth_12mo': hg_12mo,
                'website_traffic': website_traffic,
                'open_jobs_count': open_jobs_count,
                'context': self.context,
                'date_added': self.date_added
            })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    def export_contacts(self, output_path):
        """Export contacts to CSV."""
        if not self.contacts:
            return 0

        fieldnames = ['name', 'title', 'company', 'domain', 'linkedin_url',
                      'location', 'start_date', 'profile_id', 'context', 'date_added']

        rows = [{
            'name': c.get('name', ''),
            'title': c.get('latest_experience_title', ''),
            'company': c.get('latest_experience_company', ''),
            'domain': c.get('domain', ''),
            'linkedin_url': c.get('url', ''),
            'location': c.get('location_name', ''),
            'start_date': c.get('latest_experience_start_date', ''),
            'profile_id': c.get('profile_id', ''),
            'context': self.context,
            'date_added': self.date_added
        } for c in self.contacts]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    def export_jobs(self, output_path):
        """Export jobs to CSV."""
        if not self.jobs:
            return 0

        fieldnames = ['company_name', 'title', 'normalized_title', 'location',
                      'salary_min', 'salary_max', 'salary_currency', 'salary_unit',
                      'seniority', 'functions', 'employment_type',
                      'url', 'application_url', 'posted_at', 'closed_at',
                      'context', 'date_added']

        rows = [{
            'company_name': j.get('company_name', j.get('source_company_name', '')),
            'title': j.get('title', ''),
            'normalized_title': j.get('normalized_title', ''),
            'location': j.get('location', ''),
            'salary_min': j.get('salary_min', ''),
            'salary_max': j.get('salary_max', ''),
            'salary_currency': j.get('salary_currency', ''),
            'salary_unit': j.get('salary_unit', ''),
            'seniority': j.get('seniority', ''),
            'functions': ', '.join(j.get('functions', [])) if isinstance(j.get('functions'), list) else '',
            'employment_type': j.get('employment_type', ''),
            'url': j.get('url', ''),
            'application_url': j.get('application_url', ''),
            'posted_at': j.get('posted_at', ''),
            'closed_at': j.get('closed_at', ''),
            'context': self.context,
            'date_added': self.date_added
        } for j in self.jobs]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    def export_enrichments(self, output_path):
        """Export enrichments to CSV."""
        if not self.enrichments:
            return 0

        fieldnames = ['company_domain', 'company_name', 'type', 'state', 'value', 'provider',
                      'context', 'date_added']

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in self.enrichments:
                writer.writerow({
                    'company_domain': e.get('company_domain', ''),
                    'company_name': e.get('company_name', ''),
                    'type': e.get('type', ''),
                    'state': e.get('state', ''),
                    'value': e.get('value', ''),
                    'provider': e.get('provider', ''),
                    'context': self.context,
                    'date_added': self.date_added
                })
        return len(self.enrichments)

    def export_all(self, output_dir):
        """Export all data to CSV files."""
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        return {
            'companies': self.export_companies(f'{output_dir}/companies_{ts}.csv'),
            'contacts': self.export_contacts(f'{output_dir}/contacts_{ts}.csv'),
            'jobs': self.export_jobs(f'{output_dir}/jobs_{ts}.csv'),
            'enrichments': self.export_enrichments(f'{output_dir}/enrichments_{ts}.csv')
        }

    def summary(self):
        """Return summary statistics."""
        return {
            'companies': len(self.companies),
            'contacts': len(self.contacts),
            'jobs': len(self.jobs),
            'enrichments': len(self.enrichments),
            'search_ids': len(self.search_ids)
        }


# Standalone usage
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python export_clay_session.py <output_dir>")
        sys.exit(1)

    collector = ClaySessionCollector()
    results = collector.export_all(sys.argv[1])
    print(f"Exported: {results}")
