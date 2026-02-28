import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_style("whitegrid")

# Load data
df = pd.read_csv('processed_baseball_injuries.csv')
print(f"Loaded {len(df)} pitcher injuries")

# Create output directory for plots
import os
if not os.path.exists('visualizations'):
    os.makedirs('visualizations')

print("\nGenerating Velocity and Spin Rate Visualizations...")
print("="*60)

# Define time period pairs
time_pairs = [
    ('t_minus_1', 't_plus_1', 'T-1 vs T+1'),
    ('t_minus_2', 't_plus_2', 'T-2 vs T+2'),
    ('t_minus_3', 't_plus_3', 'T-3 vs T+3'),
    ('t_minus_4', 't_plus_4', 'T-4 vs T+4')
]

# ============================================================================
# VELOCITY AND SPIN RATE: BEFORE VS AFTER (ALL TIME PERIODS)
# ============================================================================

fig, axes = plt.subplots(4, 4, figsize=(20, 16))
fig.suptitle('Velocity and Spin Rate: Before vs After Surgery (Matched Pairs Only)', 
             fontsize=18, fontweight='bold', y=0.995)

for row_idx, (before_period, after_period, label) in enumerate(time_pairs):
    velocity_before_col = f'avg_velocity_{before_period}'
    velocity_after_col = f'avg_velocity_{after_period}'
    spin_before_col = f'avg_spin_rate_{before_period}'
    spin_after_col = f'avg_spin_rate_{after_period}'
    
    # Filter for matched pairs - VELOCITY
    matched_velocity = df[
        df[velocity_before_col].notna() & 
        df[velocity_after_col].notna()
    ].copy()
    
    # Filter for matched pairs - SPIN RATE
    matched_spin = df[
        df[spin_before_col].notna() & 
        df[spin_after_col].notna()
    ].copy()
    
    print(f"\n{label}:")
    print(f"  Matched velocity pairs: {len(matched_velocity)}")
    print(f"  Matched spin rate pairs: {len(matched_spin)}")
    
    # ========================================================================
    # COLUMN 1: Velocity Histogram
    # ========================================================================
    if len(matched_velocity) > 0:
        velocity_before = matched_velocity[velocity_before_col]
        velocity_after = matched_velocity[velocity_after_col]
        
        axes[row_idx, 0].hist([velocity_before, velocity_after], 
                              bins=15, 
                              label=[f'Before ({before_period.replace("_", "-").upper()})', 
                                     f'After ({after_period.replace("_", "-").upper()})'], 
                              alpha=0.7, 
                              color=['#3498db', '#e74c3c'])
        axes[row_idx, 0].set_xlabel('Velocity (mph)', fontsize=10)
        axes[row_idx, 0].set_ylabel('Frequency', fontsize=10)
        axes[row_idx, 0].set_title(f'{label} - Velocity Distribution (n={len(matched_velocity)})', 
                                   fontsize=11, fontweight='bold')
        axes[row_idx, 0].legend(fontsize=9)
        axes[row_idx, 0].grid(True, alpha=0.3)
        
        # Add mean lines
        axes[row_idx, 0].axvline(velocity_before.mean(), color='#3498db', 
                                linestyle='--', linewidth=2, alpha=0.7)
        axes[row_idx, 0].axvline(velocity_after.mean(), color='#e74c3c', 
                                linestyle='--', linewidth=2, alpha=0.7)
    
    # ========================================================================
    # COLUMN 2: Velocity Scatter Plot
    # ========================================================================
    if len(matched_velocity) > 0:
        velocity_before = matched_velocity[velocity_before_col]
        velocity_after = matched_velocity[velocity_after_col]
        
        axes[row_idx, 1].scatter(velocity_before, velocity_after, 
                                alpha=0.6, s=50, color='#3498db', edgecolors='black', linewidth=0.5)
        
        # Add reference line (no change)
        min_val = min(velocity_before.min(), velocity_after.min())
        max_val = max(velocity_before.max(), velocity_after.max())
        axes[row_idx, 1].plot([min_val, max_val], [min_val, max_val], 
                             'r--', linewidth=2, label='No Change', alpha=0.7)
        
        axes[row_idx, 1].set_xlabel(f'Velocity Before (mph)', fontsize=10)
        axes[row_idx, 1].set_ylabel(f'Velocity After (mph)', fontsize=10)
        axes[row_idx, 1].set_title(f'{label} - Velocity Change', fontsize=11, fontweight='bold')
        axes[row_idx, 1].legend(fontsize=9)
        axes[row_idx, 1].grid(True, alpha=0.3)
        
        # Calculate and display statistics
        mean_change = velocity_after.mean() - velocity_before.mean()
        axes[row_idx, 1].text(0.05, 0.95, f'Δ = {mean_change:+.2f} mph', 
                             transform=axes[row_idx, 1].transAxes,
                             fontsize=10, verticalalignment='top',
                             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # ========================================================================
    # COLUMN 3: Spin Rate Histogram
    # ========================================================================
    if len(matched_spin) > 0:
        spin_before = matched_spin[spin_before_col]
        spin_after = matched_spin[spin_after_col]
        
        axes[row_idx, 2].hist([spin_before, spin_after], 
                              bins=15, 
                              label=[f'Before ({before_period.replace("_", "-").upper()})', 
                                     f'After ({after_period.replace("_", "-").upper()})'], 
                              alpha=0.7, 
                              color=['#2ecc71', '#e67e22'])
        axes[row_idx, 2].set_xlabel('Spin Rate (rpm)', fontsize=10)
        axes[row_idx, 2].set_ylabel('Frequency', fontsize=10)
        axes[row_idx, 2].set_title(f'{label} - Spin Rate Distribution (n={len(matched_spin)})', 
                                   fontsize=11, fontweight='bold')
        axes[row_idx, 2].legend(fontsize=9)
        axes[row_idx, 2].grid(True, alpha=0.3)
        
        # Add mean lines
        axes[row_idx, 2].axvline(spin_before.mean(), color='#2ecc71', 
                                linestyle='--', linewidth=2, alpha=0.7)
        axes[row_idx, 2].axvline(spin_after.mean(), color='#e67e22', 
                                linestyle='--', linewidth=2, alpha=0.7)
    
    # ========================================================================
    # COLUMN 4: Spin Rate Scatter Plot
    # ========================================================================
    if len(matched_spin) > 0:
        spin_before = matched_spin[spin_before_col]
        spin_after = matched_spin[spin_after_col]
        
        axes[row_idx, 3].scatter(spin_before, spin_after, 
                                alpha=0.6, s=50, color='#2ecc71', edgecolors='black', linewidth=0.5)
        
        # Add reference line (no change)
        min_val = min(spin_before.min(), spin_after.min())
        max_val = max(spin_before.max(), spin_after.max())
        axes[row_idx, 3].plot([min_val, max_val], [min_val, max_val], 
                             'r--', linewidth=2, label='No Change', alpha=0.7)
        
        axes[row_idx, 3].set_xlabel(f'Spin Rate Before (rpm)', fontsize=10)
        axes[row_idx, 3].set_ylabel(f'Spin Rate After (rpm)', fontsize=10)
        axes[row_idx, 3].set_title(f'{label} - Spin Rate Change', fontsize=11, fontweight='bold')
        axes[row_idx, 3].legend(fontsize=9)
        axes[row_idx, 3].grid(True, alpha=0.3)
        
        # Calculate and display statistics
        mean_change = spin_after.mean() - spin_before.mean()
        axes[row_idx, 3].text(0.05, 0.95, f'Δ = {mean_change:+.1f} rpm', 
                             transform=axes[row_idx, 3].transAxes,
                             fontsize=10, verticalalignment='top',
                             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('visualizations/velocity_spin_before_after.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: velocity_spin_before_after.png")

# ============================================================================
# SUMMARY STATISTICS TABLE
# ============================================================================
print("\n" + "="*60)
print("SUMMARY STATISTICS (Matched Pairs Only)")
print("="*60)

summary_data = []
for before_period, after_period, label in time_pairs:
    velocity_before_col = f'avg_velocity_{before_period}'
    velocity_after_col = f'avg_velocity_{after_period}'
    spin_before_col = f'avg_spin_rate_{before_period}'
    spin_after_col = f'avg_spin_rate_{after_period}'
    
    # Velocity stats
    matched_velocity = df[
        df[velocity_before_col].notna() & 
        df[velocity_after_col].notna()
    ]
    
    if len(matched_velocity) > 0:
        v_before_mean = matched_velocity[velocity_before_col].mean()
        v_after_mean = matched_velocity[velocity_after_col].mean()
        v_change = v_after_mean - v_before_mean
    else:
        v_before_mean = v_after_mean = v_change = np.nan
    
    # Spin rate stats
    matched_spin = df[
        df[spin_before_col].notna() & 
        df[spin_after_col].notna()
    ]
    
    if len(matched_spin) > 0:
        s_before_mean = matched_spin[spin_before_col].mean()
        s_after_mean = matched_spin[spin_after_col].mean()
        s_change = s_after_mean - s_before_mean
    else:
        s_before_mean = s_after_mean = s_change = np.nan
    
    summary_data.append({
        'Comparison': label,
        'Velocity_N': len(matched_velocity),
        'Velocity_Before': v_before_mean,
        'Velocity_After': v_after_mean,
        'Velocity_Change': v_change,
        'Spin_N': len(matched_spin),
        'Spin_Before': s_before_mean,
        'Spin_After': s_after_mean,
        'Spin_Change': s_change
    })

summary_df = pd.DataFrame(summary_data)

print("\nVELOCITY:")
print("-" * 60)
print(f"{'Comparison':<15} {'N':<6} {'Before':<10} {'After':<10} {'Change':<10}")
print("-" * 60)
for _, row in summary_df.iterrows():
    print(f"{row['Comparison']:<15} {row['Velocity_N']:<6.0f} "
          f"{row['Velocity_Before']:<10.2f} {row['Velocity_After']:<10.2f} "
          f"{row['Velocity_Change']:+10.2f}")

print("\nSPIN RATE:")
print("-" * 60)
print(f"{'Comparison':<15} {'N':<6} {'Before':<10} {'After':<10} {'Change':<10}")
print("-" * 60)
for _, row in summary_df.iterrows():
    print(f"{row['Comparison']:<15} {row['Spin_N']:<6.0f} "
          f"{row['Spin_Before']:<10.1f} {row['Spin_After']:<10.1f} "
          f"{row['Spin_Change']:+10.1f}")

print("\n" + "="*60)
print("Visualization saved to 'visualizations/' directory")
print("="*60)
