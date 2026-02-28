import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import shapiro, ttest_rel, wilcoxon
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 12)

print("="*80)
print("STATISTICAL ANALYSIS: Which Pitch Types Increase/Decrease Post-Surgery?")
print("="*80)

# Load data
df = pd.read_csv('processed_baseball_injuries.csv')
print(f"\nLoaded {len(df)} pitcher injuries from dataset")

# Define pitch types
pitch_types = [
    ('ff', 'Four-Seam Fastball', '#FF6B6B'),
    ('si', 'Sinker', '#4ECDC4'),
    ('sl', 'Slider', '#45B7D1'),
    ('cu', 'Curveball', '#FFA07A'),
    ('ch', 'Changeup', '#98D8C8'),
    ('fc', 'Cutter', '#F7DC6F')
]

# Define time period pairs for analysis
time_pairs = [
    ('t_minus_1', 't_plus_1', 'T-1 vs T+1', '1 year'),
    ('t_minus_2', 't_plus_2', 'T-2 vs T+2', '2 years'),
    ('t_minus_3', 't_plus_3', 'T-3 vs T+3', '3 years'),
    ('t_minus_4', 't_plus_4', 'T-4 vs T+4', '4 years')
]

# Create output directory
import os
if not os.path.exists('analysis_results'):
    os.makedirs('analysis_results')

# ============================================================================
# PART 1: DATA PREPARATION - MATCHED PAIRS ONLY
# ============================================================================
print("\n" + "="*80)
print("PART 1: DATA PREPARATION (Matched Pairs Only)")
print("="*80)

all_results = []

for before_period, after_period, label, time_desc in time_pairs:
    print(f"\n{label} ({time_desc} before/after surgery):")
    print("-" * 80)
    
    period_results = {
        'comparison': label,
        'time_desc': time_desc,
        'pitch_results': {}
    }
    
    for pitch_code, pitch_name, color in pitch_types:
        before_col = f'{pitch_code}_pct_{before_period}'
        after_col = f'{pitch_code}_pct_{after_period}'
        
        # Filter for matched pairs
        matched = df[
            df[before_col].notna() & 
            df[after_col].notna()
        ].copy()
        
        if len(matched) == 0:
            continue
        
        before_vals = matched[before_col]
        after_vals = matched[after_col]
        diff_vals = after_vals - before_vals
        
        # ====================================================================
        # PART 2: DESCRIPTIVE STATISTICS
        # ====================================================================
        
        results = {
            'pitch_name': pitch_name,
            'pitch_code': pitch_code,
            'color': color,
            'n': len(matched),
            'before_mean': before_vals.mean(),
            'before_std': before_vals.std(),
            'before_median': before_vals.median(),
            'after_mean': after_vals.mean(),
            'after_std': after_vals.std(),
            'after_median': after_vals.median(),
            'diff_mean': diff_vals.mean(),
            'diff_std': diff_vals.std(),
            'diff_median': diff_vals.median(),
            'pct_increased': (diff_vals > 0).sum() / len(diff_vals) * 100,
            'pct_decreased': (diff_vals < 0).sum() / len(diff_vals) * 100,
            'pct_unchanged': (diff_vals == 0).sum() / len(diff_vals) * 100
        }
        
        # ====================================================================
        # PART 3: NORMALITY TESTING
        # ====================================================================
        
        if len(diff_vals) >= 3:
            stat, p_value = shapiro(diff_vals)
            results['normality_p'] = p_value
            results['is_normal'] = p_value > 0.05
        else:
            results['normality_p'] = np.nan
            results['is_normal'] = False
        
        # ====================================================================
        # PART 4: STATISTICAL TESTS
        # ====================================================================
        
        if len(diff_vals) >= 2:
            # Paired t-test (parametric)
            t_stat, t_p = ttest_rel(before_vals, after_vals)
            results['ttest_statistic'] = t_stat
            results['ttest_p'] = t_p
            
            # Wilcoxon signed-rank test (non-parametric alternative)
            if len(diff_vals) >= 10:
                try:
                    w_stat, w_p = wilcoxon(before_vals, after_vals)
                    results['wilcoxon_statistic'] = w_stat
                    results['wilcoxon_p'] = w_p
                except:
                    results['wilcoxon_statistic'] = np.nan
                    results['wilcoxon_p'] = np.nan
            else:
                results['wilcoxon_statistic'] = np.nan
                results['wilcoxon_p'] = np.nan
            
            # Cohen's d (effect size)
            if results['diff_std'] > 0:
                cohens_d = results['diff_mean'] / results['diff_std']
                results['cohens_d'] = cohens_d
            else:
                results['cohens_d'] = 0.0
            
            # 95% Confidence Interval for mean difference
            se = results['diff_std'] / np.sqrt(results['n'])
            ci_margin = 1.96 * se
            results['ci_lower'] = results['diff_mean'] - ci_margin
            results['ci_upper'] = results['diff_mean'] + ci_margin
        
        period_results['pitch_results'][pitch_code] = results
    
    all_results.append(period_results)

# ============================================================================
# PRINT DETAILED RESULTS
# ============================================================================

for period_result in all_results:
    label = period_result['comparison']
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    
    for pitch_code, pitch_name, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            r = period_result['pitch_results'][pitch_code]
            print(f"\n{pitch_name.upper()} (n={r['n']}):")
            print(f"  Before: {r['before_mean']:.2f}% ± {r['before_std']:.2f}% (median: {r['before_median']:.2f}%)")
            print(f"  After:  {r['after_mean']:.2f}% ± {r['after_std']:.2f}% (median: {r['after_median']:.2f}%)")
            print(f"  Change: {r['diff_mean']:+.2f}% ± {r['diff_std']:.2f}% (median: {r['diff_median']:+.2f}%)")
            print(f"  Direction: {r['pct_increased']:.1f}% increased | {r['pct_decreased']:.1f}% decreased | {r['pct_unchanged']:.1f}% unchanged")
            
            if 'ttest_p' in r:
                sig_text = '***' if r['ttest_p'] < 0.001 else '**' if r['ttest_p'] < 0.01 else '*' if r['ttest_p'] < 0.05 else 'ns'
                print(f"  Paired t-test: t={r['ttest_statistic']:.3f}, p={r['ttest_p']:.4f} {sig_text}")
                
                if not np.isnan(r['wilcoxon_p']):
                    sig_text_w = '***' if r['wilcoxon_p'] < 0.001 else '**' if r['wilcoxon_p'] < 0.01 else '*' if r['wilcoxon_p'] < 0.05 else 'ns'
                    print(f"  Wilcoxon test: W={r['wilcoxon_statistic']:.1f}, p={r['wilcoxon_p']:.4f} {sig_text_w}")
                
                effect_label = '(Large)' if abs(r['cohens_d']) > 0.8 else '(Medium)' if abs(r['cohens_d']) > 0.5 else '(Small)'
                print(f"  Effect size (Cohen's d): {r['cohens_d']:.3f} {effect_label}")
                print(f"  95% CI: [{r['ci_lower']:.2f}%, {r['ci_upper']:.2f}%]")

# ============================================================================
# PART 5: VISUALIZATION
# ============================================================================
print("\n" + "="*80)
print("GENERATING VISUALIZATIONS")
print("="*80)

# Create comprehensive visualization
fig = plt.figure(figsize=(20, 16))
gs = fig.add_gridspec(4, 6, hspace=0.4, wspace=0.3)

for row_idx, period_result in enumerate(all_results):
    label = period_result['comparison']
    
    for col_idx, (pitch_code, pitch_name, color) in enumerate(pitch_types):
        if pitch_code not in period_result['pitch_results']:
            continue
        
        r = period_result['pitch_results'][pitch_code]
        
        # Get the actual data
        before_period, after_period = time_pairs[row_idx][0], time_pairs[row_idx][1]
        before_col = f'{pitch_code}_pct_{before_period}'
        after_col = f'{pitch_code}_pct_{after_period}'
        
        matched = df[df[before_col].notna() & df[after_col].notna()].copy()
        diff_vals = matched[after_col] - matched[before_col]
        
        # Create subplot
        ax = fig.add_subplot(gs[row_idx, col_idx])
        
        # Histogram of differences
        ax.hist(diff_vals, bins=15, alpha=0.7, color=color, edgecolor='black')
        ax.axvline(0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='No Change')
        ax.axvline(diff_vals.mean(), color='darkblue', linestyle='-', linewidth=2, 
                   label=f'Mean: {diff_vals.mean():+.1f}%')
        
        # Labels and title
        if row_idx == 0:
            ax.set_title(f'{pitch_name}\n{label}', fontsize=10, fontweight='bold')
        else:
            ax.set_title(label, fontsize=9)
        
        if col_idx == 0:
            ax.set_ylabel('Frequency', fontsize=9)
        
        if row_idx == 3:
            ax.set_xlabel('Usage Change (%)', fontsize=9)
        
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Add statistics annotation
        if 'ttest_p' in r:
            p_val = r['ttest_p']
            sig_text = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
            stats_text = f'n={r["n"]}\np={p_val:.3f} {sig_text}\nd={r["cohens_d"]:.2f}'
            ax.text(0.05, 0.95, stats_text,
                   transform=ax.transAxes,
                   fontsize=7, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

fig.suptitle('Pitch Mix Changes After Surgery: Statistical Analysis (Matched Pairs Only)', 
             fontsize=16, fontweight='bold', y=0.995)

plt.savefig('analysis_results/pitch_mix_statistical_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: pitch_mix_statistical_analysis.png")

# ============================================================================
# PART 6: SUMMARY HEATMAP
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Pitch Mix Changes: Summary Heatmaps', fontsize=16, fontweight='bold')

# Prepare data for heatmaps
pitch_names_short = [name for _, name, _ in pitch_types]
comparison_labels = [r['comparison'] for r in all_results]

# Heatmap 1: Mean change in usage
mean_changes = []
for period_result in all_results:
    row = []
    for pitch_code, _, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            row.append(period_result['pitch_results'][pitch_code]['diff_mean'])
        else:
            row.append(np.nan)
    mean_changes.append(row)

mean_changes_df = pd.DataFrame(mean_changes, columns=pitch_names_short, index=comparison_labels)
sns.heatmap(mean_changes_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0, 
            cbar_kws={'label': 'Mean Change (%)'}, ax=axes[0, 0], vmin=-10, vmax=10)
axes[0, 0].set_title('Mean Usage Change (%)', fontweight='bold')
axes[0, 0].set_ylabel('Time Period')

# Heatmap 2: P-values
p_values = []
for period_result in all_results:
    row = []
    for pitch_code, _, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            p_val = period_result['pitch_results'][pitch_code].get('ttest_p', np.nan)
            row.append(p_val)
        else:
            row.append(np.nan)
    p_values.append(row)

p_values_df = pd.DataFrame(p_values, columns=pitch_names_short, index=comparison_labels)
sns.heatmap(p_values_df, annot=True, fmt='.3f', cmap='RdYlGn_r', 
            cbar_kws={'label': 'p-value'}, ax=axes[0, 1], vmin=0, vmax=0.1)
axes[0, 1].set_title('Statistical Significance (p-values)', fontweight='bold')
axes[0, 1].set_ylabel('Time Period')

# Heatmap 3: Effect sizes (Cohen's d)
effect_sizes = []
for period_result in all_results:
    row = []
    for pitch_code, _, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            row.append(period_result['pitch_results'][pitch_code].get('cohens_d', np.nan))
        else:
            row.append(np.nan)
    effect_sizes.append(row)

effect_sizes_df = pd.DataFrame(effect_sizes, columns=pitch_names_short, index=comparison_labels)
sns.heatmap(effect_sizes_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            cbar_kws={'label': "Cohen's d"}, ax=axes[1, 0], vmin=-1, vmax=1)
axes[1, 0].set_title('Effect Sizes (Cohen\'s d)', fontweight='bold')
axes[1, 0].set_xlabel('Pitch Type')
axes[1, 0].set_ylabel('Time Period')

# Heatmap 4: Sample sizes
sample_sizes = []
for period_result in all_results:
    row = []
    for pitch_code, _, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            row.append(period_result['pitch_results'][pitch_code]['n'])
        else:
            row.append(0)
    sample_sizes.append(row)

sample_sizes_df = pd.DataFrame(sample_sizes, columns=pitch_names_short, index=comparison_labels)
sns.heatmap(sample_sizes_df, annot=True, fmt='.0f', cmap='YlGnBu',
            cbar_kws={'label': 'Sample Size'}, ax=axes[1, 1])
axes[1, 1].set_title('Sample Sizes (Matched Pairs)', fontweight='bold')
axes[1, 1].set_xlabel('Pitch Type')
axes[1, 1].set_ylabel('Time Period')

plt.tight_layout()
plt.savefig('analysis_results/pitch_mix_summary_heatmaps.png', dpi=300, bbox_inches='tight')
print("✓ Saved: pitch_mix_summary_heatmaps.png")

# ============================================================================
# PART 7: FINAL SUMMARY REPORT
# ============================================================================
print("\n" + "="*80)
print("FINAL SUMMARY: WHICH PITCH TYPES INCREASE/DECREASE POST-SURGERY?")
print("="*80)

for period_result in all_results:
    label = period_result['comparison']
    print(f"\n{label}:")
    print("-" * 80)
    
    # Sort by mean change
    pitch_results_list = []
    for pitch_code, pitch_name, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            r = period_result['pitch_results'][pitch_code]
            pitch_results_list.append((pitch_name, r))
    
    pitch_results_list.sort(key=lambda x: x[1]['diff_mean'], reverse=True)
    
    print(f"{'Pitch Type':<20} {'Change':<12} {'p-value':<10} {'Significant':<12} {'Direction'}")
    print("-" * 80)
    
    for pitch_name, r in pitch_results_list:
        if 'ttest_p' in r:
            sig = "YES" if r['ttest_p'] < 0.05 else "NO"
            direction = "INCREASED" if r['diff_mean'] > 0 else "DECREASED" if r['diff_mean'] < 0 else "UNCHANGED"
            print(f"{pitch_name:<20} {r['diff_mean']:+6.2f}%     p={r['ttest_p']:.4f}   {sig:<12} {direction}")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)

# Identify consistent trends across all time periods
pitch_trends = {pitch_code: [] for pitch_code, _, _ in pitch_types}

for period_result in all_results:
    for pitch_code, _, _ in pitch_types:
        if pitch_code in period_result['pitch_results']:
            r = period_result['pitch_results'][pitch_code]
            if 'ttest_p' in r and r['ttest_p'] < 0.05:
                pitch_trends[pitch_code].append(r['diff_mean'])

print("\nConsistent Trends (statistically significant across multiple time periods):")
print("-" * 80)

for pitch_code, pitch_name, _ in pitch_types:
    trends = pitch_trends[pitch_code]
    if len(trends) >= 2:  # Significant in at least 2 time periods
        avg_change = np.mean(trends)
        direction = "INCREASED" if avg_change > 0 else "DECREASED"
        print(f"{pitch_name}: {direction} (avg change: {avg_change:+.2f}%, significant in {len(trends)}/4 comparisons)")

print("\n" + "="*80)
print("INTERPRETATION GUIDE:")
print("="*80)
print("""
STATISTICAL SIGNIFICANCE:
- p < 0.05: Statistically significant change
- p < 0.01: Highly significant
- p < 0.001: Very highly significant

EFFECT SIZE (Cohen's d):
- |d| > 0.8: Large effect
- |d| 0.5-0.8: Medium effect
- |d| < 0.5: Small effect

DIRECTION:
- Positive change: Pitch type used MORE after surgery
- Negative change: Pitch type used LESS after surgery

See detailed visualizations in analysis_results/ directory.
""")

print("="*80)
print("Analysis complete!")
print("="*80)
