from Conversation import Conversation
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, date

def plot_top_emojis(data):
    """
    Create a polished, Spotify Wrapped-style bar graph of top 15 emojis.
    
    Parameters:
    data: A list containing two lists [[emojis], [counts]]
    """
    emojis, counts = data[0], data[1]
    
    # Get top 15 emojis
    top_15_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)[:15]
    top_emojis = [emojis[i] for i in top_15_indices]
    top_counts = [counts[i] for i in top_15_indices]
    
    # Create gradient colors
    colors = [
        '#8B5CF6', '#7C3AED', '#6D28D9', '#5B21B6', '#4C1D95',
        '#EC4899', '#DB2777', '#BE185D', '#9D174D', '#831843',
        '#F59E0B', '#D97706', '#B45309', '#92400E', '#78350F'
    ]
    
    # Create the bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=top_emojis,
            y=top_counts,
            marker=dict(
                color=colors[:len(top_emojis)],
                line=dict(color='rgba(255,255,255,0.3)', width=1)
            ),
            text=top_counts,
            textposition='outside',
            textfont=dict(size=12, color='white', family='Arial Black'),
            hovertemplate='<b>%{x}</b><br>%{y:,} uses<extra></extra>'
        )
    ])
    
    # Update layout for modern, wrapped-style look
    fig.update_layout(
        title=dict(
            text='<b>Top 15 Most Used Emojis</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='',
            tickfont=dict(size=32, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=False
        ),
        yaxis=dict(
            title='Usage Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=40),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        )
    )
    
    fig.show()

def plot_emoji_timeline(data, title_suffix=''):
    """
    Create a polished line graph showing emoji usage over time.
    
    Parameters:
    data: Dictionary from get_emoji_timeline() with 'dates' and 'emojis' keys
    title_suffix: Optional text to add to title (e.g., sender name)
    """
    if not data['dates'] or not data['emojis']:
        print("No data to plot!")
        return
    
    # Generate colors with maximum difference using HSL color space
    def generate_distinct_colors(n):
        """Generate n maximally distinct colors"""
        colors = []
        for i in range(n):
            # Spread hues evenly across color wheel (0-360 degrees)
            hue = (i * 360 / n) % 360
            # Alternate between high and medium saturation for variety
            saturation = 85 if i % 2 == 0 else 70
            # Alternate lightness for additional distinction
            lightness = 60 if i % 3 == 0 else 55 if i % 3 == 1 else 65
            colors.append(f'hsl({hue}, {saturation}%, {lightness}%)')
        return colors
    
    num_emojis = len(data['emojis'])
    colors = generate_distinct_colors(num_emojis)
    
    fig = go.Figure()
    
    # Add a line for each emoji
    for idx, (emoji, counts) in enumerate(data['emojis'].items()):
        color = colors[idx]
        
        fig.add_trace(go.Scatter(
            x=data['dates'],
            y=counts,
            mode='lines+markers',
            name=emoji,
            line=dict(color=color, width=3),
            marker=dict(size=6, color=color, line=dict(color='white', width=1)),
            hovertemplate='<b>%{fullData.name}</b><br>%{x}<br>%{y:,} uses<extra></extra>'
        ))
    
    # Update layout for modern, wrapped-style look
    title_text = f'<b>Emoji Usage Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Usage Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        legend=dict(
            font=dict(size=20, color='white'),
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1
        ),
        hovermode='x unified'
    )
    
    fig.show()

def plot_emoji_by_hour(data, title_suffix=''):
    """
    Create a line graph showing emoji usage by hour of day.
    
    Parameters:
    data: Dictionary from get_emoji_by_hour() with 'hours' and 'emojis' keys
    title_suffix: Optional text to add to title (e.g., sender name)
    """
    if not data['emojis']:
        print("No data to plot!")
        return
    
    # Generate colors with maximum difference
    def generate_distinct_colors(n):
        colors = []
        for i in range(n):
            hue = (i * 360 / n) % 360
            saturation = 85 if i % 2 == 0 else 70
            lightness = 60 if i % 3 == 0 else 55 if i % 3 == 1 else 65
            colors.append(f'hsl({hue}, {saturation}%, {lightness}%)')
        return colors
    
    num_emojis = len(data['emojis'])
    colors = generate_distinct_colors(num_emojis)
    
    fig = go.Figure()
    
    # Add a line for each emoji
    for idx, (emoji, counts) in enumerate(data['emojis'].items()):
        color = colors[idx]
        
        fig.add_trace(go.Scatter(
            x=data['hours'],
            y=counts,
            mode='lines+markers',
            name=emoji,
            line=dict(color=color, width=3),
            marker=dict(size=7, color=color, line=dict(color='white', width=1)),
            hovertemplate='<b>%{fullData.name}</b><br>Hour: %{x}:00<br>%{y:,} uses<extra></extra>'
        ))
    
    # Update layout
    title_text = f'<b>Emoji Usage by Hour of Day</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Usage Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        legend=dict(
            font=dict(size=20, color='white'),
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1
        ),
        hovermode='x unified'
    )
    
    fig.show()

import plotly.graph_objects as go

def plot_messages_timeline(data, title_suffix=''):
    """
    Create a line graph showing message count over time.
    
    Parameters:
    data: Dictionary from get_messages_timeline() with 'dates' and 'counts' keys
    title_suffix: Optional text to add to title
    """
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['counts'],
        mode='lines+markers',
        name='Messages',
        line=dict(color='#8B5CF6', width=3),
        marker=dict(size=6, color='#8B5CF6', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)',
        hovertemplate='<b>%{x}</b><br>%{y:,} messages<extra></extra>'
    ))
    
    title_text = f'<b>Message Activity Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Message Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_messages_by_hour(data, title_suffix=''):
    """
    Create a line graph showing message count by hour of day.
    
    Parameters:
    data: Dictionary from get_messages_by_hour() with 'hours' and 'counts' keys
    title_suffix: Optional text to add to title
    """
    if not data['counts']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['hours'],
        y=data['counts'],
        mode='lines+markers',
        name='Messages',
        line=dict(color='#EC4899', width=3),
        marker=dict(size=7, color='#EC4899', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(236, 72, 153, 0.2)',
        hovertemplate='<b>Hour: %{x}:00</b><br>%{y:,} messages<extra></extra>'
    ))
    
    title_text = f'<b>Message Activity by Hour</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Message Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_top_chats_timeline(data, title_suffix=''):
    """
    Plot timeline for top chats: expects data with 'dates' and 'conversations'
    where 'conversations' is a dict mapping label -> list of counts aligned to dates.
    """
    if not data or not data.get('dates') or not data.get('conversations'):
        print('No data to plot!')
        return

    fig = go.Figure()
    colors = ['#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#06B6D4', '#F43F5E', '#A78BFA']
    for idx, (label, counts) in enumerate(data['conversations'].items()):
        fig.add_trace(go.Scatter(
            x=data['dates'],
            y=counts,
            mode='lines+markers',
            name=label,
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=6),
        ))

    title_text = f'<b>Top Chats — Messages Sent Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'

    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor='center', font=dict(size=28, color='white', family='Arial Black')),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(title='Date', title_font=dict(size=16, color='#a78bfa'), tickfont=dict(size=12, color='white')),
        yaxis=dict(title='Messages Sent', title_font=dict(size=16, color='#a78bfa'), tickfont=dict(size=12, color='white')),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(bgcolor='#1f2937', font_size=14, font_family='Arial'),
        hovermode='x unified'
    )

    fig.show()


def plot_attachments_timeline(data, title_suffix=''):
    """
    Create a line graph showing attachment count over time.
    
    Parameters:
    data: Dictionary from get_attachments_timeline() with 'dates' and 'counts' keys
    title_suffix: Optional text to add to title
    """
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['counts'],
        mode='lines+markers',
        name='Attachments',
        line=dict(color='#F59E0B', width=3),
        marker=dict(size=6, color='#F59E0B', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(245, 158, 11, 0.2)',
        hovertemplate='<b>%{x}</b><br>%{y:,} attachments<extra></extra>'
    ))
    
    title_text = f'<b>Attachment Activity Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Attachment Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_attachments_by_hour(data, title_suffix=''):
    """
    Create a line graph showing attachment count by hour of day.
    
    Parameters:
    data: Dictionary from get_attachments_by_hour() with 'hours' and 'counts' keys
    title_suffix: Optional text to add to title
    """
    if not data['counts']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['hours'],
        y=data['counts'],
        mode='lines+markers',
        name='Attachments',
        line=dict(color='#10B981', width=3),
        marker=dict(size=7, color='#10B981', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.2)',
        hovertemplate='<b>Hour: %{x}:00</b><br>%{y:,} attachments<extra></extra>'
    ))
    
    title_text = f'<b>Attachment Activity by Hour</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Attachment Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()

def plot_double_texts_timeline(data, title_suffix=''):
    """Plot double text count over time."""
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['counts'],
        mode='lines+markers',
        name='Double Texts',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=6, color='#EF4444', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(239, 68, 68, 0.2)',
        hovertemplate='<b>%{x}</b><br>%{y:,} double texts<extra></extra>'
    ))
    
    title_text = f'<b>Double Text Activity Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Double Text Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_double_texts_by_hour(data, title_suffix=''):
    """Plot double text count by hour of day."""
    if not data['counts']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['hours'],
        y=data['counts'],
        mode='lines+markers',
        name='Double Texts',
        line=dict(color='#F59E0B', width=3),
        marker=dict(size=7, color='#F59E0B', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(245, 158, 11, 0.2)',
        hovertemplate='<b>Hour: %{x}:00</b><br>%{y:,} double texts<extra></extra>'
    ))
    
    title_text = f'<b>Double Text Activity by Hour</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Double Text Count',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()

def plot_avg_time_between_double_texts_timeline(data, title_suffix='', metric_name='Median'):
    """
    Plot time between double texts over time.
    
    Parameters:
    - data: Dictionary with 'dates' and 'avg_minutes' keys
    - title_suffix: Optional suffix for title
    - metric_name: 'Median' or 'Mean' for display purposes
    """
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['avg_minutes'],
        mode='lines+markers',
        name=f'{metric_name} Time Between',
        line=dict(color='#8B5CF6', width=3),
        marker=dict(size=6, color='#8B5CF6', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)',
        hovertemplate=f'<b>%{{x}}</b><br>%{{y:.1f}} minutes {metric_name.lower()}<extra></extra>'
    ))
    
    title_text = f'<b>{metric_name} Time Between Double Texts</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=f'{metric_name} Minutes',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_avg_time_between_double_texts_by_hour(data, title_suffix='', metric_name='Median'):
    """
    Plot time between double texts by hour of day.
    
    Parameters:
    - data: Dictionary with 'hours' and 'avg_minutes' keys
    - title_suffix: Optional suffix for title
    - metric_name: 'Median' or 'Mean' for display purposes
    """
    if not data['avg_minutes']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['hours'],
        y=data['avg_minutes'],
        mode='lines+markers',
        name=f'{metric_name} Time Between',
        line=dict(color='#EC4899', width=3),
        marker=dict(size=7, color='#EC4899', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(236, 72, 153, 0.2)',
        hovertemplate=f'<b>Hour: %{{x}}:00</b><br>%{{y:.1f}} minutes {metric_name.lower()}<extra></extra>'
    ))
    
    title_text = f'<b>{metric_name} Time Between Double Texts by Hour</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=f'{metric_name} Minutes',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()

def plot_avg_response_time_timeline(data, title_suffix='', metric_name='Median'):
    """
    Plot response time over time.
    
    Parameters:
    - data: Dictionary with 'dates' and 'avg_minutes' keys
    - title_suffix: Optional suffix for title
    - metric_name: 'Median' or 'Mean' for display purposes
    """
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['avg_minutes'],
        mode='lines+markers',
        name=f'{metric_name} Response Time',
        line=dict(color='#10B981', width=3),
        marker=dict(size=6, color='#10B981', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.2)',
        hovertemplate=f'<b>%{{x}}</b><br>%{{y:.1f}} minutes {metric_name.lower()}<extra></extra>'
    ))
    
    title_text = f'<b>{metric_name} Response Time Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=f'{metric_name} Response Time (minutes)',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_avg_response_time_by_hour(data, title_suffix='', metric_name='Median'):
    """
    Plot response time by hour of day.
    
    Parameters:
    - data: Dictionary with 'hours' and 'avg_minutes' keys
    - title_suffix: Optional suffix for title
    - metric_name: 'Median' or 'Mean' for display purposes
    """
    if not data['avg_minutes']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['hours'],
        y=data['avg_minutes'],
        mode='lines+markers',
        name=f'{metric_name} Response Time',
        line=dict(color='#06B6D4', width=3),
        marker=dict(size=7, color='#06B6D4', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(6, 182, 212, 0.2)',
        hovertemplate=f'<b>Hour: %{{x}}:00</b><br>%{{y:.1f}} minutes {metric_name.lower()}<extra></extra>'
    ))
    
    title_text = f'<b>{metric_name} Response Time by Hour of Day</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day (When Message Was Sent)',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=f'{metric_name} Response Time (minutes)',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()

def plot_sent_received_ratio_timeline(data, title_suffix=''):
    """
    Plot the ratio of messages sent vs received over time.
    Red fill when sending more than receiving (ratio > 0.5)
    Green fill when receiving more than sending (ratio < 0.5)
    
    Parameters:
    - data: Dictionary with 'dates', 'ratios', 'sent_counts', 'received_counts' keys
    - title_suffix: Optional suffix for title
    """
    if not data['dates']:
        print("No data to plot!")
        return
    
    dates = data['dates']
    ratios = data['ratios']
    sent_counts = data['sent_counts']
    received_counts = data['received_counts']
    
    fig = go.Figure()
    
    # Debug: Print original data
    print("="*80)
    print("ORIGINAL DATA:")
    print(f"Number of points: {len(dates)}")
    for i in range(min(10, len(dates))):
        print(f"  [{i}] Date: {dates[i]}, Ratio: {ratios[i]:.3f}")
    if len(dates) > 10:
        print(f"  ... ({len(dates) - 10} more points)")
    print()
    
    # Build expanded segments that include interpolated crossing points
    expanded_dates = []
    expanded_ratios = []
    
    # Track if we're using date or datetime objects
    using_dates = isinstance(dates[0], date) and not isinstance(dates[0], datetime)
    
    for i in range(len(dates)):
        # Convert date to datetime if needed for consistent handling
        if using_dates:
            expanded_dates.append(datetime.combine(dates[i], datetime.min.time()))
        else:
            expanded_dates.append(dates[i])
        expanded_ratios.append(ratios[i])
        
        # Check if line crosses 0.5 between this point and next
        if i < len(dates) - 1:
            current_ratio = ratios[i]
            next_ratio = ratios[i + 1]
            
            # Check if crosses 0.5
            if (current_ratio > 0.5 and next_ratio < 0.5) or (current_ratio < 0.5 and next_ratio > 0.5):
                # Interpolate the crossing point
                # Linear interpolation: find where ratio = 0.5
                t = (0.5 - current_ratio) / (next_ratio - current_ratio)
                
                # At this point, expanded_dates already contains datetime objects
                # So we can do simple datetime arithmetic
                date_diff = expanded_dates[i] - expanded_dates[i]  # Will be recalculated below
                
                # Get the actual dates we just added
                current_expanded = expanded_dates[-1]
                if using_dates:
                    next_expanded = datetime.combine(dates[i + 1], datetime.min.time())
                else:
                    next_expanded = dates[i + 1]
                
                date_diff = next_expanded - current_expanded
                crossing_date = current_expanded + date_diff * t
                
                expanded_dates.append(crossing_date)
                expanded_ratios.append(0.5)
    
    # Debug: Print expanded data with crossings
    print("EXPANDED DATA (with interpolated crossings):")
    print(f"Number of points: {len(expanded_dates)}")
    for i in range(min(15, len(expanded_dates))):
        date_str = str(expanded_dates[i])
        print(f"  [{i}] Date: {date_str}, Ratio: {expanded_ratios[i]:.3f}")
    if len(expanded_dates) > 15:
        print(f"  ... ({len(expanded_dates) - 15} more points)")
    
    # Check if crossings have unique dates
    crossing_indices = [i for i in range(len(expanded_ratios)) if expanded_ratios[i] == 0.5]
    print(f"\nCrossing points (at 0.5): {len(crossing_indices)}")
    for idx in crossing_indices[:5]:
        if idx > 0:
            prev_date = expanded_dates[idx-1]
            curr_date = expanded_dates[idx]
            next_date = expanded_dates[idx+1] if idx+1 < len(expanded_dates) else None
            print(f"  Crossing at index {idx}:")
            print(f"    Previous: {prev_date}")
            print(f"    Crossing: {curr_date}")
            print(f"    Next: {next_date}")
            print(f"    Is between? {prev_date < curr_date < next_date if next_date else 'N/A'}")
    print()
    
    # Now separate into red and green segments
    # Strategy: Walk through and build segments including proper crossings
    red_segments = []
    green_segments = []
    
    i = 0
    while i < len(expanded_dates):
        ratio = expanded_ratios[i]
        
        if ratio == 0.5:
            # This is a crossing point - look ahead to see what zone we're entering
            if i + 1 < len(expanded_dates):
                next_ratio = expanded_ratios[i + 1]
                
                if next_ratio > 0.5:
                    # Entering red zone - start red segment with this crossing
                    seg_dates = [expanded_dates[i]]
                    seg_ratios = [expanded_ratios[i]]
                    i += 1
                    
                    # Continue collecting red points
                    while i < len(expanded_dates) and expanded_ratios[i] > 0.5:
                        seg_dates.append(expanded_dates[i])
                        seg_ratios.append(expanded_ratios[i])
                        i += 1
                    
                    # Add ending crossing point if we hit one
                    if i < len(expanded_dates) and expanded_ratios[i] == 0.5:
                        seg_dates.append(expanded_dates[i])
                        seg_ratios.append(expanded_ratios[i])
                        # Don't increment - next iteration will handle this crossing
                    
                    if len(seg_dates) >= 2:
                        red_segments.append((seg_dates, seg_ratios))
                
                elif next_ratio < 0.5:
                    # Entering green zone - start green segment with this crossing
                    seg_dates = [expanded_dates[i]]
                    seg_ratios = [expanded_ratios[i]]
                    i += 1
                    
                    # Continue collecting green points
                    while i < len(expanded_dates) and expanded_ratios[i] < 0.5:
                        seg_dates.append(expanded_dates[i])
                        seg_ratios.append(expanded_ratios[i])
                        i += 1
                    
                    # Add ending crossing point if we hit one
                    if i < len(expanded_dates) and expanded_ratios[i] == 0.5:
                        seg_dates.append(expanded_dates[i])
                        seg_ratios.append(expanded_ratios[i])
                        # Don't increment - next iteration will handle this crossing
                    
                    if len(seg_dates) >= 2:
                        green_segments.append((seg_dates, seg_ratios))
                else:
                    # Next point is also 0.5, skip this one
                    i += 1
            else:
                i += 1
        
        elif ratio > 0.5:
            # We shouldn't start here unless we're at the very beginning
            # Start red segment without a crossing point
            seg_dates = [expanded_dates[i]]
            seg_ratios = [expanded_ratios[i]]
            i += 1
            
            while i < len(expanded_dates) and expanded_ratios[i] > 0.5:
                seg_dates.append(expanded_dates[i])
                seg_ratios.append(expanded_ratios[i])
                i += 1
            
            if i < len(expanded_dates) and expanded_ratios[i] == 0.5:
                seg_dates.append(expanded_dates[i])
                seg_ratios.append(expanded_ratios[i])
            
            if len(seg_dates) >= 2:
                red_segments.append((seg_dates, seg_ratios))
        
        elif ratio < 0.5:
            # We shouldn't start here unless something went wrong
            # Start green segment without a crossing point
            seg_dates = [expanded_dates[i]]
            seg_ratios = [expanded_ratios[i]]
            i += 1
            
            while i < len(expanded_dates) and expanded_ratios[i] < 0.5:
                seg_dates.append(expanded_dates[i])
                seg_ratios.append(expanded_ratios[i])
                i += 1
            
            if i < len(expanded_dates) and expanded_ratios[i] == 0.5:
                seg_dates.append(expanded_dates[i])
                seg_ratios.append(expanded_ratios[i])
            
            if len(seg_dates) >= 2:
                green_segments.append((seg_dates, seg_ratios))
        
        else:
            i += 1
    
    # Debug: Print segment information
    print("SEGMENTS FOUND:")
    print(f"Red segments (above 0.5): {len(red_segments)}")
    for idx, (seg_dates, seg_ratios) in enumerate(red_segments):
        print(f"  Red segment {idx}: {len(seg_dates)} points, ratios: {min(seg_ratios):.3f} to {max(seg_ratios):.3f}")
        if len(seg_dates) <= 5:
            print(f"    Points: {seg_ratios}")
    
    print(f"Green segments (below 0.5): {len(green_segments)}")
    for idx, (seg_dates, seg_ratios) in enumerate(green_segments):
        print(f"  Green segment {idx}: {len(seg_dates)} points, ratios: {min(seg_ratios):.3f} to {max(seg_ratios):.3f}")
        if len(seg_dates) <= 5:
            print(f"    Points: {seg_ratios}")
    print("="*80)
    print()
    
    # Draw red segments
    for seg_dates, seg_ratios in red_segments:
        if len(seg_dates) > 0:
            x_coords = list(seg_dates) + list(reversed(seg_dates))
            y_coords = list(seg_ratios) + [0.5] * len(seg_dates)
            
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                fill='toself',
                fillcolor='rgba(239, 68, 68, 0.4)',
                line=dict(color='rgba(0,0,0,0)', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Draw green segments
    for seg_dates, seg_ratios in green_segments:
        if len(seg_dates) > 0:
            x_coords = list(seg_dates) + list(reversed(seg_dates))
            y_coords = list(seg_ratios) + [0.5] * len(seg_dates)
            
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                fill='toself',
                fillcolor='rgba(16, 185, 129, 0.4)',
                line=dict(color='rgba(0,0,0,0)', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add the main line and markers on top
    hover_texts = []
    # Use original dates for hover (not expanded datetime versions)
    for i in range(len(dates)):
        sent = sent_counts[i]
        received = received_counts[i]
        ratio = ratios[i]
        balance_text = "Sending more" if ratio > 0.5 else "Receiving more" if ratio < 0.5 else "Equal"
        
        hover_texts.append(
            f'<b>{dates[i]}</b><br>'
            f'Ratio: {ratio:.2%}<br>'
            f'Sent: {sent:,} messages<br>'
            f'Received: {received:,} messages<br>'
            f'{balance_text}'
        )
    
    # Convert dates to datetime for plotting if needed
    plot_dates = [datetime.combine(d, datetime.min.time()) if using_dates else d for d in dates]
    
    fig.add_trace(go.Scatter(
        x=plot_dates,
        y=ratios,
        mode='lines+markers',
        line=dict(color='white', width=3),
        marker=dict(
            size=8,
            color=ratios,
            colorscale=[
                [0.0, 'rgb(16, 185, 129)'],   # Green at 0
                [0.5, 'rgb(128, 128, 128)'],   # Gray at 0.5
                [1.0, 'rgb(239, 68, 68)']      # Red at 1
            ],
            cmin=0,
            cmax=1,
            line=dict(color='white', width=2),
            showscale=False
        ),
        showlegend=False,
        hovertemplate='%{text}<extra></extra>',
        text=hover_texts
    ))
    
    # Add reference line at 0.5 (equal balance)
    fig.add_hline(
        y=0.5, 
        line_dash="dash", 
        line_color="rgba(255,255,255,0.5)",
        line_width=2,
        annotation_text="Equal Balance",
        annotation_position="right",
        annotation_font_size=12,
        annotation_font_color="rgba(255,255,255,0.7)"
    )
    
    # Create legend items
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=12, color='rgba(239, 68, 68, 0.8)', line=dict(color='white', width=2)),
        name='Sending More',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=12, color='rgba(16, 185, 129, 0.8)', line=dict(color='white', width=2)),
        name='Receiving More',
        showlegend=True
    ))
    
    title_text = '<b>Message Balance: Sent vs Received</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Ratio (Sent / Total)',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            tickformat='.0%',
            range=[0, 1]
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        legend=dict(
            font=dict(size=14, color='white'),
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1,
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top'
        ),
        hovermode='closest'
    )
    
    fig.show()

def plot_total_words_timeline(data, title_suffix=''):
    """Plot total word count over time."""
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['counts'],
        mode='lines+markers',
        name='Total Words',
        line=dict(color='#F59E0B', width=3),
        marker=dict(size=6, color='#F59E0B', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(245, 158, 11, 0.2)',
        hovertemplate='<b>%{x}</b><br>%{y:,} words<extra></extra>'
    ))
    
    title_text = f'<b>Total Words Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Total Words',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_words_per_message_timeline(data, title_suffix='', metric_name='Median'):
    """Plot average words per message over time."""
    if not data['dates']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['avg_words'],
        mode='lines+markers',
        name=f'{metric_name} Words/Message',
        line=dict(color='#8B5CF6', width=3),
        marker=dict(size=6, color='#8B5CF6', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)',
        hovertemplate=f'<b>%{{x}}</b><br>%{{y:.1f}} words/message {metric_name.lower()}<extra></extra>'
    ))
    
    title_text = f'<b>{metric_name} Words Per Message Over Time</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Date',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=f'{metric_name} Words Per Message',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()


def plot_words_per_message_by_hour(data, title_suffix='', metric_name='Median'):
    """Plot average words per message by hour of day."""
    if not data['avg_words']:
        print("No data to plot!")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['hours'],
        y=data['avg_words'],
        mode='lines+markers',
        name=f'{metric_name} Words/Message',
        line=dict(color='#EC4899', width=3),
        marker=dict(size=7, color='#EC4899', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(236, 72, 153, 0.2)',
        hovertemplate=f'<b>Hour: %{{x}}:00</b><br>%{{y:.1f}} words/message {metric_name.lower()}<extra></extra>'
    ))
    
    title_text = f'<b>{metric_name} Words Per Message by Hour</b>'
    if title_suffix:
        title_text += f'<br><sub>{title_suffix}</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=32, color='white', family='Arial Black')
        ),
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white', size=14),
        xaxis=dict(
            title='Hour of Day',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=f'{metric_name} Words Per Message',
            title_font=dict(size=16, color='#a78bfa'),
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hoverlabel=dict(
            bgcolor='#1f2937',
            font_size=14,
            font_family='Arial'
        ),
        hovermode='x unified'
    )
    
    fig.show()

if __name__ == "__main__":
    c = Conversation("exports/chat_573.json")
    #c.printConvo()
    #print(c.thread[1].sender_name)
    c.calculate_statistics()
    #print(c.senders)
    #plot_top_emojis(c.get_emoji_totals("You"))
    #plot_emoji_timeline(c.get_emoji_timeline(period="day", top_n=5))
    #plot_emoji_by_hour(c.get_emoji_by_hour(top_n=10))
    # Messages over time - weekly
    data = c.get_messages_timeline(sender_number="You", period='day')
    #plot_messages_timeline(data, title_suffix='Daily Activity')

    # Messages by hour
    data = c.get_messages_by_hour(sender_number="You")
    #plot_messages_by_hour(data, title_suffix='Your Messaging Patterns')

    # Attachments over time - monthly
    data = c.get_attachments_timeline(period='day')
    #plot_attachments_timeline(data, title_suffix='Daily Attachments')

    # Attachments by hour
    data = c.get_attachments_by_hour(sender_number="You")
    #plot_attachments_by_hour(data, title_suffix='When You Share Media')

    # Double text count over time
    data = c.get_double_texts_timeline(sender_number="You", period='hour')
    #plot_double_texts_timeline(data, title_suffix='Your Double Texting - Hourly')

    # Double text count by hour
    data = c.get_double_texts_by_hour(sender_number="You")
    #plot_double_texts_by_hour(data, title_suffix='When You Double Text')

    # Average time between double texts over time
    data = c.get_avg_time_between_double_texts_timeline(sender_number="You", period='day')
    #plot_avg_time_between_double_texts_timeline(data, title_suffix='Hourly Average')

    # Average time between double texts by hour
    data = c.get_avg_time_between_double_texts_by_hour(sender_number="You")
    #plot_avg_time_between_double_texts_by_hour(data, title_suffix='How Long Between Your Double Texts')
    
    data = c.double_text_stats.get_sent_received_ratio_timeline(sender_number="You", period='week')
    #plot_sent_received_ratio_timeline(data, title_suffix='Your Messaging Balance')

    # Median response time over time (default, more robust)
    data = c.get_avg_response_time_timeline(sender_number="You", period='week')
    #plot_avg_response_time_timeline(data, title_suffix='Your Response Time - Weekly', metric_name='Median')

    # Mean response time if you prefer
    data = c.get_avg_response_time_timeline(sender_number="You", period='week', use_median=False)
    #plot_avg_response_time_timeline(data, title_suffix='Your Response Time - Weekly', metric_name='Mean')

    # Median response time by hour of day
    data = c.get_avg_response_time_by_hour(sender_number="You")
    #plot_avg_response_time_by_hour(data, title_suffix='How Fast You Respond by Hour', metric_name='Median')

    # Daily median response time
    data = c.get_avg_response_time_timeline(sender_number="You", period='day')
    #plot_avg_response_time_timeline(data, title_suffix='Daily Response Time', metric_name='Median')

    # Total words over time
    data = c.get_total_words_timeline(sender_number="You", period='week')
    plot_total_words_timeline(data, title_suffix='Your Word Usage - Weekly')

    # Median words per message over time
    data = c.get_words_per_message_timeline(sender_number="You", period='week')
    plot_words_per_message_timeline(data, title_suffix='Weekly', metric_name='Median')

    # Median words per message by hour
    data = c.get_words_per_message_by_hour(sender_number="You")
    plot_words_per_message_by_hour(data, title_suffix='Your Texting Style', metric_name='Median')

    # Get overall average
    avg_words = c.get_overall_avg_words_per_message(sender_number="You")
    print(f"Your overall median words per message: {avg_words:.1f}")