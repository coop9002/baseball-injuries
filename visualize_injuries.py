import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Load data
df = pd.read_csv('processed_baseball_injuries.csv')
print(f"Loaded {len(df)} pitcher injuries")

# Create output directory for plots
import os
if not os.path.exists('visualizations'):
    os.makedirs('visualizations')

print("\nGenerating visualizations...")
print("="*60)

# ============================================================================
# 1. PERFORMANCE METRICS - Before vs After Surgery
# ============================================================================
print("\n1. Performance Metrics (Before vs After)")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Performance Metrics: Before vs After Surgery', fontsize=16, fontweight='bold')

# Velocity comparison
velocity_before = df['avg_velocity_t_minus_1'].dropna()
velocity_after = df['avg_velocity_t_plus_1'].dropna()
axes[0, 0].hist([velocity_before, velocity_after], bins=20, label=['Before (T-1)', 'After (T+1)'], alpha=0.7, color=['blue', 'red'])
axes[0, 0].set_xlabel('Velocity (mph)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Pitch Velocity Distribution')
axes[0, 0].legend()

# Spin rate comparison
spin_before = df['avg_spin_rate_t_minus_1'].dropna()
spin_after = df['avg_spin_rate_t_plus_1'].dropna()
axes[0, 1].hist([spin_before, spin_after], bins=20, label=['Before (T-1)', 'After (T+1)'], alpha=0.7, color=['blue', 'red'])
axes[0, 1].set_xlabel('Spin Rate (rpm)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Spin Rate Distribution')
axes[0, 1].legend()

# Games started comparison
gs_before = df['gs_t_minus_1'].dropna()
gs_after = df['gs_t_plus_1'].dropna()
axes[0, 2].hist([gs_before, gs_after], bins=20, label=['Before (T-1)', 'After (T+1)'], alpha=0.7, color=['blue', 'red'])
axes[0, 2].set_xlabel('Games Started')
axes[0, 2].set_ylabel('Frequency')
axes[0, 2].set_title('Games Started Distribution')
axes[0, 2].legend()

# Velocity change scatter
matched_velocity = df[df['avg_velocity_t_minus_1'].notna() & df['avg_velocity_t_plus_1'].notna()]
if len(matched_velocity) > 0:
    axes[1, 0].scatter(matched_velocity['avg_velocity_t_minus_1'], matched_velocity['avg_velocity_t_plus_1'], alpha=0.5, color='steelblue')
    min_val = min(matched_velocity['avg_velocity_t_minus_1'].min(), matched_velocity['avg_velocity_t_plus_1'].min())
    max_val = max(matched_velocity['avg_velocity_t_minus_1'].max(), matched_velocity['avg_velocity_t_plus_1'].max())
    axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='No Change')
    axes[1, 0].set_xlabel('Velocity Before (T-1)')
    axes[1, 0].set_ylabel('Velocity After (T+1)')
    axes[1, 0].set_title(f'Velocity Change (n={len(matched_velocity)})')
    axes[1, 0].legend()

# Spin rate change scatter
matched_spin = df[df['avg_spin_rate_t_minus_1'].notna() & df['avg_spin_rate_t_plus_1'].notna()]
if len(matched_spin) > 0:
    axes[1, 1].scatter(matched_spin['avg_spin_rate_t_minus_1'], matched_spin['avg_spin_rate_t_plus_1'], alpha=0.5, color='coral')
    min_val = min(matched_spin['avg_spin_rate_t_minus_1'].min(), matched_spin['avg_spin_rate_t_plus_1'].min())
    max_val = max(matched_spin['avg_spin_rate_t_minus_1'].max(), matched_spin['avg_spin_rate_t_plus_1'].max())
    axes[1, 1].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='No Change')
    axes[1, 1].set_xlabel('Spin Rate Before (T-1)')
    axes[1, 1].set_ylabel('Spin Rate After (T+1)')
    axes[1, 1].set_title(f'Spin Rate Change (n={len(matched_spin)})')
    axes[1, 1].legend()

# Role change (Starter vs Reliever)
matched_role = df[df['gs_t_minus_1'].notna() & df['gs_t_plus_1'].notna()]
if len(matched_role) > 0:
    axes[1, 2].scatter(matched_role['gs_t_minus_1'], matched_role['gs_t_plus_1'], alpha=0.5, color='mediumseagreen')
    min_val = 0
    max_val = max(matched_role['gs_t_minus_1'].max(), matched_role['gs_t_plus_1'].max())
    axes[1, 2].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='No Change')
    axes[1, 2].set_xlabel('Games Started Before (T-1)')
    axes[1, 2].set_ylabel('Games Started After (T+1)')
    axes[1, 2].set_title(f'Role Change (n={len(matched_role)})')
    axes[1, 2].legend()

plt.tight_layout()
plt.savefig('visualizations/1_before_after_comparison.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: 1_before_after_comparison.png")

# ============================================================================
# 2. RECOVERY TRAJECTORY - Performance over time
# ============================================================================
print("\n2. Recovery Trajectory")

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle('Recovery Trajectory: T-4 to T+4', fontsize=16, fontweight='bold')

time_periods = ['t_minus_4', 't_minus_3', 't_minus_2', 't_minus_1', 't_plus_1', 't_plus_2', 't_plus_3', 't_plus_4']
time_labels = ['T-4', 'T-3', 'T-2', 'T-1', 'T+1', 'T+2', 'T+3', 'T+4']

# Velocity trajectory
velocity_means = []
velocity_stds = []
for period in time_periods:
    col = f'avg_velocity_{period}'
    if col in df.columns:
        data = df[col].dropna()
        velocity_means.append(data.mean() if len(data) > 0 else np.nan)
        velocity_stds.append(data.std() if len(data) > 0 else np.nan)

axes[0, 0].plot(time_labels, velocity_means, marker='o', linewidth=2, color='steelblue', markersize=8)
axes[0, 0].fill_between(range(len(time_labels)), 
                         np.array(velocity_means) - np.array(velocity_stds),
                         np.array(velocity_means) + np.array(velocity_stds),
                         alpha=0.2, color='steelblue')
axes[0, 0].axvline(x=3.5, color='red', linestyle='--', linewidth=2, label='Surgery')
axes[0, 0].set_xlabel('Time Period')
axes[0, 0].set_ylabel('Average Velocity (mph)')
axes[0, 0].set_title('Velocity Trajectory')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Spin rate trajectory
spin_means = []
spin_stds = []
for period in time_periods:
    col = f'avg_spin_rate_{period}'
    if col in df.columns:
        data = df[col].dropna()
        spin_means.append(data.mean() if len(data) > 0 else np.nan)
        spin_stds.append(data.std() if len(data) > 0 else np.nan)

axes[0, 1].plot(time_labels, spin_means, marker='o', linewidth=2, color='coral', markersize=8)
axes[0, 1].fill_between(range(len(time_labels)), 
                         np.array(spin_means) - np.array(spin_stds),
                         np.array(spin_means) + np.array(spin_stds),
                         alpha=0.2, color='coral')
axes[0, 1].axvline(x=3.5, color='red', linestyle='--', linewidth=2, label='Surgery')
axes[0, 1].set_xlabel('Time Period')
axes[0, 1].set_ylabel('Average Spin Rate (rpm)')
axes[0, 1].set_title('Spin Rate Trajectory')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Games started trajectory
gs_means = []
for period in time_periods:
    col = f'gs_{period}'
    if col in df.columns:
        data = df[col].dropna()
        gs_means.append(data.mean() if len(data) > 0 else np.nan)

axes[1, 0].plot(time_labels, gs_means, marker='o', linewidth=2, color='mediumseagreen', markersize=8)
axes[1, 0].axvline(x=3.5, color='red', linestyle='--', linewidth=2, label='Surgery')
axes[1, 0].set_xlabel('Time Period')
axes[1, 0].set_ylabel('Average Games Started')
axes[1, 0].set_title('Games Started Trajectory')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Relief appearances trajectory
relief_means = []
for period in time_periods:
    col = f'relief_app_{period}'
    if col in df.columns:
        data = df[col].dropna()
        relief_means.append(data.mean() if len(data) > 0 else np.nan)

axes[1, 1].plot(time_labels, relief_means, marker='o', linewidth=2, color='purple', markersize=8)
axes[1, 1].axvline(x=3.5, color='red', linestyle='--', linewidth=2, label='Surgery')
axes[1, 1].set_xlabel('Time Period')
axes[1, 1].set_ylabel('Average Relief Appearances')
axes[1, 1].set_title('Relief Appearances Trajectory')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('visualizations/2_recovery_trajectory.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: 2_recovery_trajectory.png")

# ============================================================================
# 3. PITCH MIX ANALYSIS
# ============================================================================
print("\n3. Pitch Mix Analysis")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Pitch Mix: Before vs After Surgery', fontsize=16, fontweight='bold')

pitch_types = ['ff', 'si', 'sl', 'cu', 'ch', 'fc']
pitch_names = ['Four-Seam FB', 'Sinker', 'Slider', 'Curveball', 'Changeup', 'Cutter']
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']

for idx, (pitch_type, pitch_name, color) in enumerate(zip(pitch_types, pitch_names, colors)):
    row = idx // 3
    col = idx % 3
    
    before_col = f'{pitch_type}_pct_t_minus_1'
    after_col = f'{pitch_type}_pct_t_plus_1'
    
    if before_col in df.columns and after_col in df.columns:
        before_data = df[before_col].dropna()
        after_data = df[after_col].dropna()
        
        # Only plot if there's data
        if len(before_data) > 0 or len(after_data) > 0:
            axes[row, col].hist([before_data, after_data], bins=15, 
                               label=['Before (T-1)', 'After (T+1)'], 
                               alpha=0.7, color=[color, 'gray'])
            axes[row, col].set_xlabel('Usage %')
            axes[row, col].set_ylabel('Frequency')
            axes[row, col].set_title(f'{pitch_name}')
            axes[row, col].legend()

plt.tight_layout()
plt.savefig('visualizations/3_pitch_mix_analysis.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: 3_pitch_mix_analysis.png")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\nSummary Statistics:")
print("-" * 60)

# Calculate average changes
velocity_change = matched_velocity['avg_velocity_t_plus_1'].mean() - matched_velocity['avg_velocity_t_minus_1'].mean()
spin_change = matched_spin['avg_spin_rate_t_plus_1'].mean() - matched_spin['avg_spin_rate_t_minus_1'].mean()
gs_change = matched_role['gs_t_plus_1'].mean() - matched_role['gs_t_minus_1'].mean()

print(f"  Total Injuries: {len(df)}")
print(f"  With Velocity Data: {len(matched_velocity)}")
print(f"  With Spin Data: {len(matched_spin)}")
print(f"\n  Average Changes (T-1 to T+1):")
print(f"    Velocity: {velocity_change:+.2f} mph")
print(f"    Spin Rate: {spin_change:+.1f} rpm")
print(f"    Games Started: {gs_change:+.1f}")

print("\n" + "="*60)
print("All visualizations saved to 'visualizations/' directory")
print("="*60)
