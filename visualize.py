"""
Visualization Script
Generates charts for sentiment and framing analysis from analyzed_data.csv.
Compares YouTube comment sentiment across different channel bias categories.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "analyzed_data.csv"
OUTPUT_DIR = "charts"

sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12

COLORS = {
    "JUSTIFIED": "#2ecc71",
    "EXCESSIVE": "#e74c3c",
    "NEUTRAL": "#95a5a6",
    "MORALITY": "#9b59b6",
    "CONFLICT": "#e67e22",
    "LEGALITY": "#3498db",
    "LEFT": "#3498db",
    "RIGHT": "#e74c3c",
    "MAINSTREAM": "#95a5a6",
    "LOCAL": "#f39c12",
    "UNKNOWN": "#7f8c8d"
}

def load_data():
    """Load and validate analyzed data."""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file '{INPUT_FILE}' not found.")
        print("   Please run analyze.py first.")
        return None
    
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} analyzed comments")
    
    df = df[df['category'].isin(['JUSTIFIED', 'EXCESSIVE', 'NEUTRAL'])]
    df = df[df['frame'].isin(['MORALITY', 'CONFLICT', 'LEGALITY'])]
    
    print(f"   Valid entries after filtering: {len(df)}")
    return df

def create_sentiment_by_bias(df):
    """
    Chart 1: Sentiment by Channel Bias
    Bar chart comparing JUSTIFIED vs EXCESSIVE counts across LEFT vs RIGHT leaning channels.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    sentiment_counts = df.groupby(['bias', 'category']).size().unstack(fill_value=0)
    
    ax1 = axes[0]
    sentiment_counts.plot(kind='bar', ax=ax1, color=[COLORS.get(c, '#333') for c in sentiment_counts.columns])
    ax1.set_title('Sentiment Distribution by Channel Bias', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Channel Bias Category', fontsize=12)
    ax1.set_ylabel('Number of Comments', fontsize=12)
    ax1.legend(title='Category', bbox_to_anchor=(1.02, 1), loc='upper left')
    ax1.tick_params(axis='x', rotation=45)
    
    focus_biases = ['LEFT', 'RIGHT']
    focus_df = df[df['bias'].isin(focus_biases)]
    
    if len(focus_df) > 0:
        ax2 = axes[1]
        focus_counts = focus_df.groupby(['bias', 'category']).size().unstack(fill_value=0)
        focus_counts.plot(kind='bar', ax=ax2, color=[COLORS.get(c, '#333') for c in focus_counts.columns])
        ax2.set_title('Comparison: Left-Leaning vs Right-Leaning Channels', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Channel Bias', fontsize=12)
        ax2.set_ylabel('Number of Comments', fontsize=12)
        ax2.legend(title='Category')
        ax2.tick_params(axis='x', rotation=0)
    else:
        ax2 = axes[1]
        top_biases = df['bias'].value_counts().head(2).index.tolist()
        if len(top_biases) >= 2:
            focus_df = df[df['bias'].isin(top_biases)]
            focus_counts = focus_df.groupby(['bias', 'category']).size().unstack(fill_value=0)
            focus_counts.plot(kind='bar', ax=ax2, color=[COLORS.get(c, '#333') for c in focus_counts.columns])
            ax2.set_title('Comparison: Top Channel Categories', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Channel Bias', fontsize=12)
            ax2.set_ylabel('Number of Comments', fontsize=12)
            ax2.legend(title='Category')
            ax2.tick_params(axis='x', rotation=0)
    
    plt.tight_layout()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'sentiment_by_bias.png')
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"📊 Saved: {filepath}")
    plt.close()

def create_framing_analysis(df):
    """
    Chart 2: Framing Analysis
    Shows which channel bias categories use LEGALITY vs MORALITY frames.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    ax1 = axes[0]
    frame_counts = df.groupby(['bias', 'frame']).size().unstack(fill_value=0)
    frame_counts.plot(kind='bar', ax=ax1, color=[COLORS.get(c, '#333') for c in frame_counts.columns])
    ax1.set_title('Framing Distribution by Channel Bias', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Channel Bias Category', fontsize=12)
    ax1.set_ylabel('Number of Comments', fontsize=12)
    ax1.legend(title='Frame', bbox_to_anchor=(1.02, 1), loc='upper left')
    ax1.tick_params(axis='x', rotation=45)
    
    ax2 = axes[1]
    frame_pct = df.groupby(['bias', 'frame']).size().unstack(fill_value=0)
    frame_pct = frame_pct.div(frame_pct.sum(axis=1), axis=0) * 100
    
    frame_pct.plot(kind='barh', stacked=True, ax=ax2, 
                   color=[COLORS.get(c, '#333') for c in frame_pct.columns])
    ax2.set_title('Frame Distribution (%) by Channel Bias', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Percentage', fontsize=12)
    ax2.set_ylabel('Channel Bias Category', fontsize=12)
    ax2.legend(title='Frame', bbox_to_anchor=(1.02, 1), loc='upper left')
    ax2.set_xlim(0, 100)
    
    plt.tight_layout()
    
    filepath = os.path.join(OUTPUT_DIR, 'framing_analysis.png')
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"📊 Saved: {filepath}")
    plt.close()

def create_summary_stats(df):
    """Generate summary statistics and save to file."""
    summary = []
    summary.append("="*60)
    summary.append("ANALYSIS SUMMARY - Renee Good ICE Shooting (YouTube)")
    summary.append("="*60)
    summary.append(f"\nTotal comments analyzed: {len(df)}")
    
    summary.append("\n--- SENTIMENT DISTRIBUTION ---")
    for cat in ['JUSTIFIED', 'EXCESSIVE', 'NEUTRAL']:
        count = len(df[df['category'] == cat])
        pct = count / len(df) * 100 if len(df) > 0 else 0
        summary.append(f"  {cat}: {count} ({pct:.1f}%)")
    
    summary.append("\n--- FRAMING DISTRIBUTION ---")
    for frame in ['MORALITY', 'CONFLICT', 'LEGALITY']:
        count = len(df[df['frame'] == frame])
        pct = count / len(df) * 100 if len(df) > 0 else 0
        summary.append(f"  {frame}: {count} ({pct:.1f}%)")
    
    summary.append("\n--- BY CHANNEL BIAS ---")
    for bias in df['bias'].unique():
        bias_df = df[df['bias'] == bias]
        summary.append(f"\n{bias} channels (n={len(bias_df)}):")
        
        top_cat = bias_df['category'].value_counts().idxmax() if len(bias_df) > 0 else "N/A"
        top_frame = bias_df['frame'].value_counts().idxmax() if len(bias_df) > 0 else "N/A"
        summary.append(f"  Dominant sentiment: {top_cat}")
        summary.append(f"  Dominant frame: {top_frame}")
    
    summary_text = "\n".join(summary)
    print(summary_text)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'summary_stats.txt')
    with open(filepath, 'w') as f:
        f.write(summary_text)
    print(f"\n📄 Saved: {filepath}")

def create_heatmap(df):
    """Create a heatmap showing relationship between sentiment and framing."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    cross_tab = pd.crosstab(df['category'], df['frame'])
    
    sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlOrRd', ax=ax,
                cbar_kws={'label': 'Count'})
    ax.set_title('Sentiment vs Framing Relationship', fontsize=14, fontweight='bold')
    ax.set_xlabel('Frame', fontsize=12)
    ax.set_ylabel('Category', fontsize=12)
    
    plt.tight_layout()
    
    filepath = os.path.join(OUTPUT_DIR, 'sentiment_frame_heatmap.png')
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"📊 Saved: {filepath}")
    plt.close()

def main():
    """Main visualization pipeline."""
    print("="*60)
    print("VISUALIZATION - Generating Analysis Charts")
    print("="*60 + "\n")
    
    df = load_data()
    if df is None or len(df) == 0:
        print("❌ No valid data to visualize.")
        return
    
    print("\nGenerating visualizations...\n")
    
    create_sentiment_by_bias(df)
    create_framing_analysis(df)
    create_heatmap(df)
    create_summary_stats(df)
    
    print("\n" + "="*60)
    print(f"✅ All visualizations saved to '{OUTPUT_DIR}/' directory")
    print("="*60)

if __name__ == "__main__":
    main()
