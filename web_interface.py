#!/usr/bin/env python3
"""
Web interface for Telegram Group Management Bot
Provides a dashboard for monitoring and managing the bot
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime, timedelta
from bot.storage import storage
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'telegram-bot-web-interface')

@app.route('/')
def dashboard():
    """Main dashboard"""
    try:
        # Get basic stats
        stats = get_bot_stats()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error=str(e))

@app.route('/groups')
def groups():
    """Groups management page"""
    try:
        groups_data = storage.groups_data
        groups_list = []
        
        for group_id, group_data in groups_data.items():
            group_info = {
                'id': group_id,
                'name': group_data.get('name', f'Group {group_id}'),
                'settings': group_data.get('settings', {}),
                'banned_words': len(group_data.get('banned_words', [])),
                'log_channel': group_data.get('log_channel', 'Not set'),
                'member_count': group_data.get('member_count', 0)
            }
            groups_list.append(group_info)
        
        return render_template('groups.html', groups=groups_list)
    except Exception as e:
        logger.error(f"Error loading groups: {e}")
        return render_template('error.html', error=str(e))

@app.route('/group/<group_id>')
def group_detail(group_id):
    """Group detail page"""
    try:
        group_data = storage.get_group_data(int(group_id))
        return render_template('group_detail.html', group_id=group_id, group_data=group_data)
    except Exception as e:
        logger.error(f"Error loading group {group_id}: {e}")
        return render_template('error.html', error=str(e))

@app.route('/logs')
def logs():
    """Logs viewing page"""
    try:
        # Get recent logs
        logs_data = get_recent_logs()
        return render_template('logs.html', logs=logs_data)
    except Exception as e:
        logger.error(f"Error loading logs: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics"""
    try:
        stats = get_bot_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/group/<group_id>/settings', methods=['POST'])
def update_group_settings(group_id):
    """Update group settings"""
    try:
        data = request.get_json()
        group_data = storage.get_group_data(int(group_id))
        
        if 'settings' in data:
            group_data.setdefault('settings', {}).update(data['settings'])
            storage.save_group_data(int(group_id), group_data)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_bot_stats():
    """Get bot statistics"""
    try:
        groups_data = storage.groups_data
        spam_data = storage.spam_data
        users_data = storage.users_data
        
        stats = {
            'total_groups': len(groups_data),
            'total_users': len(users_data),
            'active_groups': sum(1 for g in groups_data.values() if g.get('settings', {}).get('anti_spam_enabled', True)),
            'spam_messages_blocked': sum(user_data.get('spam_count', 0) for user_data in spam_data.values()),
            'total_warnings': sum(user_data.get('warnings', {}).get('count', 0) for user_data in spam_data.values()),
            'captcha_enabled_groups': sum(1 for g in groups_data.values() if g.get('settings', {}).get('captcha_enabled', False)),
            'groups_with_logging': sum(1 for g in groups_data.values() if g.get('log_channel')),
            'banned_words_total': sum(len(g.get('banned_words', [])) for g in groups_data.values())
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {}

def get_recent_logs(limit=100):
    """Get recent log entries"""
    try:
        # This would read from a log file or database
        # For now, return sample data structure
        logs = []
        
        # Try to read from actual logs if available
        groups_data = storage.groups_data
        for group_id, group_data in groups_data.items():
            if 'recent_actions' in group_data:
                for action in group_data['recent_actions'][-10:]:  # Last 10 actions per group
                    logs.append({
                        'timestamp': action.get('timestamp', 'Unknown'),
                        'group_id': group_id,
                        'group_name': group_data.get('name', f'Group {group_id}'),
                        'action': action.get('action', 'unknown'),
                        'user_id': action.get('user_id', 'Unknown'),
                        'details': action.get('reason', 'No details')
                    })
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:limit]
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return []

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)