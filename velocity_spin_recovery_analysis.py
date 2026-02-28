import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import shapiro, normaltest, ttest_rel, wilcoxon
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

print("="*80)
print("STATISTICAL ANALYSIS: Do Pitchers Regain Pre-Surgery Velocity and Spin Rate?")
print("="*80)

# Load data
df = pd.read_csv('processed_baseball_injuries.csv')
print(f"\nLoaded {len(df)} pitcher injuries from dataset")

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

results_summary = []

for before_period, after_period, label, time_desc in time_pairs:
    print(f"\n{label} ({time_desc} before/after surgery):")
    print("-" * 80)
    
    velocity_before_col = f'avg_velocity_{before_period}'
    velocity_after_col = f'avg_velocity_{after_period}'
    spin_before_col = f'avg_spin_rate_{before_period}'
    spin_after_col = f'avg_spin_rate_{after_period}'
    
    # Filter for matched pairs - VELOCITY
    velocity_matched = df[
        df[velocity_before_col].notna() & 
        df[velocity_after_col].notna()
    ].copy()
    
    # Filter for matched pairs - SPIN RATE
    spin_matched = df[
        df[spin_before_col].notna() & 
        df[spin_after_col].notna()
    ].copy()
    
    print(f"  Velocity matched pairs: {len(velocity_matched)}")
    print(f"  Spin rate matched pairs: {len(spin_matched)}")
    
    if len(velocity_matched) == 0 and len(spin_matched) == 0:
        print("  ⚠ No matched pairs available - skipping this comparison")
        continue
    
    # ========================================================================
    # PART 2: DESCRIPTIVE STATISTICS
    # ========================================================================
    
    velocity_results = {}
    spin_results = {}
    
    if len(velocity_matched) > 0:
        v_before = velocity_matched[velocity_before_col]
        v_after = velocity_matched[velocity_after_col]
        v_diff = v_after - v_before
        
        velocity_results = {
            'n': len(velocity_matched),
            'before_mean': v_before.mean(),
            'before_std': v_before.std(),
            'after_mean': v_after.mean(),
            'after_std': v_after.std(),
            'diff_mean': v_diff.mean(),
            'diff_std': v_diff.std(),
            'diff_median': v_diff.median(),
            'pct_improved': (v_diff > 0).sum() / len(v_diff) * 100,
            'pct_declined': (v_diff < 0).sum() / len(v_diff) * 100,
            'pct_unchanged': (v_diff == 0).sum() / len(v_diff) * 100
        }
        
        print(f"\n  VELOCITY (n={velocity_results['n']}):")
        print(f"    Before: {velocity_results['before_mean']:.2f} ± {velocity_results['before_std']:.2f} mph")
        print(f"    After:  {velocity_results['after_mean']:.2f} ± {velocity_results['after_std']:.2f} mph")
        print(f"    Change: {velocity_results['diff_mean']:+.2f} ± {velocity_results['diff_std']:.2f} mph (median: {velocity_results['diff_median']:+.2f})")
        print(f"    Improved: {velocity_results['pct_improved']:.1f}% | Declined: {velocity_results['pct_declined']:.1f}% | Unchanged: {velocity_results['pct_unchanged']:.1f}%")
    
    if len(spin_matched) > 0:
        s_before = spin_matched[spin_before_col]
        s_after = spin_matched[spin_after_col]
        s_diff = s_after - s_before
        
        spin_results = {
            'n': len(spin_matched),
            'before_mean': s_before.mean(),
            'before_std': s_before.std(),
            'after_mean': s_after.mean(),
            'after_std': s_after.std(),
            'diff_mean': s_diff.mean(),
            'diff_std': s_diff.std(),
            'diff_median': s_diff.median(),
            'pct_improved': (s_diff > 0).sum() / len(s_diff) * 100,
            'pct_declined': (s_diff < 0).sum() / len(s_diff) * 100,
            'pct_unchanged': (s_diff == 0).sum() / len(s_diff) * 100
        }
        
        print(f"\n  SPIN RATE (n={spin_results['n']}):")
        print(f"    Before: {spin_results['before_mean']:.1f} ± {spin_results['before_std']:.1f} rpm")
        print(f"    After:  {spin_results['after_mean']:.1f} ± {spin_results['after_std']:.1f} rpm")
        print(f"    Change: {spin_results['diff_mean']:+.1f} ± {spin_results['diff_std']:.1f} rpm (median: {spin_results['diff_median']:+.1f})")
        print(f"    Improved: {spin_results['pct_improved']:.1f}% | Declined: {spin_results['pct_declined']:.1f}% | Unchanged: {spin_results['pct_unchanged']:.1f}%")
    
    # ========================================================================
    # PART 3: NORMALITY TESTING
    # ========================================================================
    print(f"\n  NORMALITY TESTS (Shapiro-Wilk):")
    
    if len(velocity_matched) > 0:
        # Test normality of differences
        if len(v_diff) >= 3:
            stat, p_value = shapiro(v_diff)
            velocity_results['normality_p'] = p_value
            velocity_results['is_normal'] = p_value > 0.05
            print(f"    Velocity differences: p={p_value:.4f} {'(Normal)' if p_value > 0.05 else '(Non-normal)'}")
        else:
            velocity_results['normality_p'] = np.nan
            velocity_results['is_normal'] = False
    
    if len(spin_matched) > 0:
        if len(s_diff) >= 3:
            stat, p_value = shapiro(s_diff)
            spin_results['normality_p'] = p_value
            spin_results['is_normal'] = p_value > 0.05
            print(f"    Spin rate differences: p={p_value:.4f} {'(Normal)' if p_value > 0.05 else '(Non-normal)'}")
        else:
            spin_results['normality_p'] = np.nan
            spin_results['is_normal'] = False
    
    # ========================================================================
    # PART 4: STATISTICAL TESTS
    # ========================================================================
    print(f"\n  STATISTICAL TESTS:")
    
    if len(velocity_matched) > 0:
        # Paired t-test (parametric)
        if len(v_diff) >= 2:
            t_stat, t_p = ttest_rel(v_before, v_after)
            velocity_results['ttest_statistic'] = t_stat
            velocity_results['ttest_p'] = t_p
            
            # Wilcoxon signed-rank test (non-parametric alternative)
            if len(v_diff) >= 10:  # Need sufficient sample for Wilcoxon
                w_stat, w_p = wilcoxon(v_before, v_after)
                velocity_results['wilcoxon_statistic'] = w_stat
                velocity_results['wilcoxon_p'] = w_p
            else:
                velocity_results['wilcoxon_statistic'] = np.nan
                velocity_results['wilcoxon_p'] = np.nan
            
            # Cohen's d (effect size)
            cohens_d = velocity_results['diff_mean'] / velocity_results['diff_std']
            velocity_results['cohens_d'] = cohens_d
            
            # 95% Confidence Interval for mean difference
            se = velocity_results['diff_std'] / np.sqrt(velocity_results['n'])
            ci_margin = 1.96 * se
            velocity_results['ci_lower'] = velocity_results['diff_mean'] - ci_margin
            velocity_results['ci_upper'] = velocity_results['diff_mean'] + ci_margin
            
            print(f"    Velocity:")
            print(f"      Paired t-test: t={t_stat:.3f}, p={t_p:.4f} {'***' if t_p < 0.001 else '**' if t_p < 0.01 else '*' if t_p < 0.05 else 'ns'}")
            if not np.isnan(velocity_results['wilcoxon_p']):
                print(f"      Wilcoxon test: W={w_stat:.1f}, p={w_p:.4f} {'***' if w_p < 0.001 else '**' if w_p < 0.01 else '*' if w_p < 0.05 else 'ns'}")
            print(f"      Effect size (Cohen's d): {cohens_d:.3f} {'(Large)' if abs(cohens_d) > 0.8 else '(Medium)' if abs(cohens_d) > 0.5 else '(Small)'}")
            print(f"      95% CI: [{velocity_results['ci_lower']:.2f}, {velocity_results['ci_upper']:.2f}] mph")
    
    if len(spin_matched) > 0:
        # Paired t-test (parametric)
        if len(s_diff) >= 2:
            t_stat, t_p = ttest_rel(s_before, s_after)
            spin_results['ttest_statistic'] = t_stat
            spin_results['ttest_p'] = t_p
            
            # Wilcoxon signed-rank test (non-parametric alternative)
            if len(s_diff) >= 10:
                w_stat, w_p = wilcoxon(s_before, s_after)
                spin_results['wilcoxon_statistic'] = w_stat
                spin_results['wilcoxon_p'] = w_p
            else:
                spin_results['wilcoxon_statistic'] = np.nan
                spin_results['wilcoxon_p'] = np.nan
            
            # Cohen's d (effect size)
            cohens_d = spin_results['diff_mean'] / spin_results['diff_std']
            spin_results['cohens_d'] = cohens_d
            
            # 95% Confidence Interval for mean difference
            se = spin_results['diff_std'] / np.sqrt(spin_results['n'])
            ci_margin = 1.96 * se
            spin_results['ci_lower'] = spin_results['diff_mean'] - ci_margin
            spin_results['ci_upper'] = spin_results['diff_mean'] + ci_margin
            
            print(f"    Spin Rate:")
            print(f"      Paired t-test: t={t_stat:.3f}, p={t_p:.4f} {'***' if t_p < 0.001 else '**' if t_p < 0.01 else '*' if t_p < 0.05 else 'ns'}")
            if not np.isnan(spin_results['wilcoxon_p']):
                print(f"      Wilcoxon test: W={w_stat:.1f}, p={w_p:.4f} {'***' if w_p < 0.001 else '**' if w_p < 0.01 else '*' if w_p < 0.05 else 'ns'}")
            print(f"      Effect size (Cohen's d): {cohens_d:.3f} {'(Large)' if abs(cohens_d) > 0.8 else '(Medium)' if abs(cohens_d) > 0.5 else '(Small)'}")
            print(f"      95% CI: [{spin_results['ci_lower']:.1f}, {spin_results['ci_upper']:.1f}] rpm")
    
    # Store results
    results_summary.append({
        'comparison': label,
        'time_desc': time_desc,
        'velocity': velocity_results,
        'spin': spin_results
    })

# ============================================================================
# PART 5: VISUALIZATION
# ============================================================================
print("\n" + "="*80)
print("PART 5: GENERATING VISUALIZATIONS")
print("="*80)

fig, axes = plt.subplots(4, 4, figsize=(20, 16))
fig.suptitle('Statistical Analysis: Velocity and Spin Rate Recovery After Surgery\n(Matched Pairs Only)', 
             fontsize=16, fontweight='bold', y=0.995)

for row_idx, result in enumerate(results_summary):
    label = result['comparison']
    v_res = result['velocity']
    s_res = result['spin']
    
    before_period, after_period = time_pairs[row_idx][0], time_pairs[row_idx][1]
    
    # Get data
    velocity_before_col = f'avg_velocity_{before_period}'
    velocity_after_col = f'avg_velocity_{after_period}'
    spin_before_col = f'avg_spin_rate_{before_period}'
    spin_after_col = f'avg_spin_rate_{after_period}'
    
    velocity_matched = df[df[velocity_before_col].notna() & df[velocity_after_col].notna()].copy()
    spin_matched = df[df[spin_before_col].notna() & df[spin_after_col].notna()].copy()
    
    # Column 1: Velocity difference distribution
    if len(velocity_matched) > 0:
        v_diff = velocity_matched[velocity_after_col] - velocity_matched[velocity_before_col]
        axes[row_idx, 0].hist(v_diff, bins=20, alpha=0.7, color='steelblue', edgecolor='black')
        axes[row_idx, 0].axvline(0, color='red', linestyle='--', linewidth=2, label='No Change')
        axes[row_idx, 0].axvline(v_diff.mean(), color='darkblue', linestyle='-', linewidth=2, label=f'Mean: {v_diff.mean():+.2f}')
        axes[row_idx, 0].set_xlabel('Velocity Change (mph)')
        axes[row_idx, 0].set_ylabel('Frequency')
        axes[row_idx, 0].set_title(f'{label} - Velocity Δ (n={len(v_diff)})')
        axes[row_idx, 0].legend(fontsize=8)
        axes[row_idx, 0].grid(True, alpha=0.3)
        
        # Add p-value annotation
        if 'ttest_p' in v_res:
            p_val = v_res['ttest_p']
            sig_text = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
            axes[row_idx, 0].text(0.95, 0.95, f'p={p_val:.4f} {sig_text}',
                                 transform=axes[row_idx, 0].transAxes,
                                 fontsize=9, verticalalignment='top', horizontalalignment='right',
                                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    # Column 2: Velocity before vs after
    if len(velocity_matched) > 0:
        v_before = velocity_matched[velocity_before_col]
        v_after = velocity_matched[velocity_after_col]
        axes[row_idx, 1].scatter(v_before, v_after, alpha=0.5, s=40, color='steelblue', edgecolors='black', linewidth=0.5)
        min_val = min(v_before.min(), v_after.min())
        max_val = max(v_before.max(), v_after.max())
        axes[row_idx, 1].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, alpha=0.7)
        axes[row_idx, 1].set_xlabel('Before (mph)')
        axes[row_idx, 1].set_ylabel('After (mph)')
        axes[row_idx, 1].set_title(f'{label} - Velocity')
        axes[row_idx, 1].grid(True, alpha=0.3)
    
    # Column 3: Spin rate difference distribution
    if len(spin_matched) > 0:
        s_diff = spin_matched[spin_after_col] - spin_matched[spin_before_col]
        axes[row_idx, 2].hist(s_diff, bins=20, alpha=0.7, color='coral', edgecolor='black')
        axes[row_idx, 2].axvline(0, color='red', linestyle='--', linewidth=2, label='No Change')
        axes[row_idx, 2].axvline(s_diff.mean(), color='darkred', linestyle='-', linewidth=2, label=f'Mean: {s_diff.mean():+.1f}')
        axes[row_idx, 2].set_xlabel('Spin Rate Change (rpm)')
        axes[row_idx, 2].set_ylabel('Frequency')
        axes[row_idx, 2].set_title(f'{label} - Spin Rate Δ (n={len(s_diff)})')
        axes[row_idx, 2].legend(fontsize=8)
        axes[row_idx, 2].grid(True, alpha=0.3)
        
        # Add p-value annotation
        if 'ttest_p' in s_res:
            p_val = s_res['ttest_p']
            sig_text = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
            axes[row_idx, 2].text(0.95, 0.95, f'p={p_val:.4f} {sig_text}',
                                 transform=axes[row_idx, 2].transAxes,
                                 fontsize=9, verticalalignment='top', horizontalalignment='right',
                                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    # Column 4: Spin rate before vs after
    if len(spin_matched) > 0:
        s_before = spin_matched[spin_before_col]
        s_after = spin_matched[spin_after_col]
        axes[row_idx, 3].scatter(s_before, s_after, alpha=0.5, s=40, color='coral', edgecolors='black', linewidth=0.5)
        min_val = min(s_before.min(), s_after.min())
        max_val = max(s_before.max(), s_after.max())
        axes[row_idx, 3].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, alpha=0.7)
        axes[row_idx, 3].set_xlabel('Before (rpm)')
        axes[row_idx, 3].set_ylabel('After (rpm)')
        axes[row_idx, 3].set_title(f'{label} - Spin Rate')
        axes[row_idx, 3].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analysis_results/velocity_spin_statistical_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: velocity_spin_statistical_analysis.png")

# ============================================================================
# PART 6: SUMMARY REPORT
# ============================================================================
print("\n" + "="*80)
print("PART 6: FINAL SUMMARY - DO PITCHERS REGAIN PRE-SURGERY PERFORMANCE?")
print("="*80)

print("\n📊 VELOCITY RECOVERY:")
print("-" * 80)
for result in results_summary:
    if result['velocity']:
        v = result['velocity']
        label = result['comparison']
        if 'ttest_p' in v:
            sig = "YES" if v['ttest_p'] < 0.05 else "NO"
            direction = "DECREASED" if v['diff_mean'] < 0 else "INCREASED" if v['diff_mean'] > 0 else "UNCHANGED"
            print(f"{label:12} | Change: {v['diff_mean']:+6.2f} mph | p={v['ttest_p']:.4f} | Significant: {sig:3} | Direction: {direction}")

print("\n📊 SPIN RATE RECOVERY:")
print("-" * 80)
for result in results_summary:
    if result['spin']:
        s = result['spin']
        label = result['comparison']
        if 'ttest_p' in s:
            sig = "YES" if s['ttest_p'] < 0.05 else "NO"
            direction = "DECREASED" if s['diff_mean'] < 0 else "INCREASED" if s['diff_mean'] > 0 else "UNCHANGED"
            print(f"{label:12} | Change: {s['diff_mean']:+7.1f} rpm | p={s['ttest_p']:.4f} | Significant: {sig:3} | Direction: {direction}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("""
Based on paired t-tests with matched samples:

VELOCITY:
- Statistical tests show whether velocity changes are significantly different from zero
- Negative changes indicate velocity loss; positive indicate velocity gain
- p < 0.05 indicates statistically significant change
- Effect sizes (Cohen's d) quantify magnitude of change

SPIN RATE:
- Similar interpretation as velocity
- Changes measured in rpm (revolutions per minute)

INTERPRETATION GUIDE:
- p < 0.05: Statistically significant change
- Cohen's d > 0.8: Large effect size
- Cohen's d 0.5-0.8: Medium effect size
- Cohen's d < 0.5: Small effect size

See detailed statistics above and visualization in analysis_results/ directory.
""")

print("="*80)
print("Analysis complete!")
print("="*80)
