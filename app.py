import math
import altair as alt
import pandas as pd
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Smart Calculator",
    page_icon="🧮",
    layout="centered",
)

# 2. Custom Styling for the Result Display Card
st.markdown(
    """
    <style>
    .result-card {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
        border: 1px solid #c7d2fe;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-top: 16px;
        margin-bottom: 16px;
    }
    .result-label {
        font-size: 0.9rem;
        color: #4f46e5;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .result-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e1b4b;
        margin: 8px 0;
    }
    .result-formula {
        font-size: 0.95rem;
        color: #64748b;
        font-family: monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper function to compute default min/max range for any variable
def get_default_bounds(val):
    if val > 0:
        return 0.0, float(val * 2.0)
    elif val < 0:
        return float(val * 2.0), 0.0
    return -10.0, 10.0

# Simple numerical root finder (Brent's method / bisection fallback) for Goal Seek
def goal_seek(func, target, low, high, max_iter=100, tol=1e-7):
    try:
        f_low = func(low) - target
        f_high = func(high) - target
    except Exception:
        return None, "Error evaluating function at boundary points."

    if math.isnan(f_low) or math.isnan(f_high):
        return None, "Function resulted in undefined values at boundaries."

    if abs(f_low) < tol:
        return low, None
    if abs(f_high) < tol:
        return high, None

    if f_low * f_high > 0:
        # Try expanding search bracket if signs don't bracket the target
        span = high - low
        if span == 0:
            span = 10.0
        expanded = False
        for mult in [2, 5, 10, 50, 100]:
            new_low = low - span * mult
            new_high = high + span * mult
            try:
                f_low = func(new_low) - target
                f_high = func(new_high) - target
                if not (math.isnan(f_low) or math.isnan(f_high)) and f_low * f_high <= 0:
                    low, high = new_low, new_high
                    expanded = True
                    break
            except Exception:
                continue
        if not expanded:
            return None, "Target value is outside the range of possible outputs for this interval. Try widening the Min/Max search bounds."

    for _ in range(max_iter):
        mid = (low + high) / 2.0
        try:
            f_mid = func(mid) - target
        except Exception:
            return None, "Math error during calculation steps."

        if math.isnan(f_mid):
            return None, "Encountered undefined mathematical result during search."

        if abs(f_mid) < tol or (high - low) / 2.0 < tol:
            return mid, None

        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    return (low + high) / 2.0, None

# 3. Header
st.title("🧮 Not-so Smart Web Calculator")
st.caption("Results, sensitivity analysis, and goal seek optimization update automatically.")

# Initialize session state for variables if not present
if "val_a" not in st.session_state:
    st.session_state.val_a = 1000.0
if "val_b" not in st.session_state:
    st.session_state.val_b = 0.05
if "val_c" not in st.session_state:
    st.session_state.val_c = 10.0

# Initialize calculation history in session state
if "history" not in st.session_state:
    st.session_state.history = []

# 4. Mode Tabs
tab_standard, tab_custom, tab_goalseek = st.tabs(
    ["🔢 Standard Calculator", "📐 Custom Formula & Sensitivity", "🎯 Goal Seek Solver"]
)

with tab_standard:
    col1, col2 = st.columns(2)
    with col1:
        num1 = st.number_input("First Number (A)", value=10.0, step=1.0, format="%.4f")
    with col2:
        num2 = st.number_input("Second Number (B)", value=5.0, step=1.0, format="%.4f")

    operation = st.selectbox(
        "Choose an Operation",
        [
            "Addition (A + B)",
            "Subtraction (A - B)",
            "Multiplication (A × B)",
            "Division (A ÷ B)",
            "Power / Exponent (A ^ B)",
            "Percentage (A% of B)",
        ],
    )

    result = None
    formula_str = ""
    error_msg = None

    if operation == "Addition (A + B)":
        result = num1 + num2
        formula_str = f"{num1:g} + {num2:g}"
    elif operation == "Subtraction (A - B)":
        result = num1 - num2
        formula_str = f"{num1:g} - {num2:g}"
    elif operation == "Multiplication (A × B)":
        result = num1 * num2
        formula_str = f"{num1:g} × {num2:g}"
    elif operation == "Division (A ÷ B)":
        if num2 == 0:
            error_msg = "Cannot divide by zero. Please enter a non-zero Second Number (B)."
        else:
            result = num1 / num2
            formula_str = f"{num1:g} ÷ {num2:g}"
    elif operation == "Power / Exponent (A ^ B)":
        try:
            result = math.pow(num1, num2)
            formula_str = f"{num1:g} ^ {num2:g}"
        except (ValueError, OverflowError) as e:
            error_msg = f"Math error: {e}"
    elif operation == "Percentage (A% of B)":
        result = (num1 / 100.0) * num2
        formula_str = f"{num1:g}% of {num2:g}"

    if error_msg:
        st.error(error_msg)
    elif result is not None:
        formatted_result = f"{result:,.6g}"
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">Instant Result</div>
                <div class="result-value">{formatted_result}</div>
                <div class="result-formula">{formula_str} = {formatted_result}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("📌 Save to History", key="save_std"):
            st.session_state.history.insert(0, f"{formula_str} = {formatted_result}")

with tab_custom:
    st.markdown(
        "Define up to three variables (**a**, **b**, **c**) and write your own formula."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        a = st.number_input("Variable a", value=st.session_state.val_a, step=10.0, key="input_a")
    with c2:
        b = st.number_input("Variable b", value=st.session_state.val_b, step=0.01, format="%.4f", key="input_b")
    with c3:
        c = st.number_input("Variable c", value=st.session_state.val_c, step=1.0, key="input_c")

    # Sync back to session state
    st.session_state.val_a = a
    st.session_state.val_b = b
    st.session_state.val_c = c

    preset = st.selectbox(
        "Quick Formula Presets",
        [
            "Compound Interest: a * (1 + b) ** c",
            "Pythagorean Hypotenuse: sqrt(a**2 + b**2)",
            "Average of Three Numbers: (a + b + c) / 3",
            "Custom (Type your own below)",
        ],
    )

    default_expr = {
        "Compound Interest: a * (1 + b) ** c": "a * (1 + b) ** c",
        "Pythagorean Hypotenuse: sqrt(a**2 + b**2)": "sqrt(a**2 + b**2)",
        "Average of Three Numbers: (a + b + c) / 3": "(a + b + c) / 3",
        "Custom (Type your own below)": "(a + b) * c",
    }[preset]

    expression = st.text_input("Formula Expression", value=default_expr)
    st.caption(
        "Supported operators: `+`, `-`, `*`, `/`, `**` (power), and functions like `sqrt()`, `sin()`, `cos()`, `log()`, `abs()`, `round()`."
    )

    # Safe dictionary of allowed math variables and functions
    allowed_names = {
        "a": a,
        "b": b,
        "c": c,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
    }

    if expression.strip():
        try:
            custom_result = float(eval(expression, {"__builtins__": {}}, allowed_names))
            formatted_custom = f"{custom_result:,.6g}"
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="result-label">Custom Formula Result</div>
                    <div class="result-value">{formatted_custom}</div>
                    <div class="result-formula">{expression} (where a={a:g}, b={b:g}, c={c:g})</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("📌 Save to History", key="save_cust"):
                st.session_state.history.insert(
                    0, f"{expression} [a={a:g}, b={b:g}, c={c:g}] = {formatted_custom}"
                )

            st.divider()
            viz_1d, viz_2d = st.tabs(
                ["📈 1D Sensitivity Curve", "🟦 2D Sensitivity Heatmap & Table"]
            )

            # --- 1D Sensitivity Curve ---
            with viz_1d:
                st.caption(
                    "Vary a single input along the horizontal axis. The red dot marks your current setting."
                )
                var_choice = st.radio(
                    "Variable on Horizontal Axis (X-Axis)",
                    options=["a", "b", "c"],
                    index=2,
                    key="radio_1d",
                    horizontal=True,
                )

                current_val = {"a": a, "b": b, "c": c}[var_choice]
                default_min, default_max = get_default_bounds(current_val)
                step_size_input = 0.01 if (0 < abs(current_val) < 1) else 1.0

                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    min_val = st.number_input(
                        f"Minimum '{var_choice}'",
                        value=default_min,
                        step=step_size_input,
                        format="%.4f",
                        key=f"min_1d_{var_choice}",
                    )
                with r_col2:
                    max_val = st.number_input(
                        f"Maximum '{var_choice}'",
                        value=default_max,
                        step=step_size_input,
                        format="%.4f",
                        key=f"max_1d_{var_choice}",
                    )

                if min_val >= max_val:
                    st.warning("Please set the Minimum value lower than the Maximum value.")
                else:
                    num_points = 100
                    step_delta = (max_val - min_val) / (num_points - 1)
                    rows = []
                    for i in range(num_points):
                        x_val = min_val + i * step_delta
                        env = dict(allowed_names)
                        env[var_choice] = x_val
                        try:
                            y_val = float(eval(expression, {"__builtins__": {}}, env))
                            if math.isfinite(y_val):
                                rows.append({var_choice: x_val, "Result": y_val})
                        except Exception:
                            pass

                    if rows:
                        df_curve = pd.DataFrame(rows)
                        line = (
                            alt.Chart(df_curve)
                            .mark_line(color="#4f46e5", strokeWidth=3)
                            .encode(
                                x=alt.X(f"{var_choice}:Q", title=f"Variable {var_choice}"),
                                y=alt.Y(
                                    "Result:Q",
                                    title="Formula Output",
                                    scale=alt.Scale(zero=False),
                                ),
                                tooltip=[
                                    alt.Tooltip(
                                        f"{var_choice}:Q",
                                        title=f"Variable {var_choice}",
                                        format=",.4f",
                                    ),
                                    alt.Tooltip("Result:Q", title="Result", format=",.4f"),
                                ],
                            )
                        )

                        if min_val <= current_val <= max_val and math.isfinite(custom_result):
                            df_current = pd.DataFrame(
                                [{var_choice: float(current_val), "Result": float(custom_result)}]
                            )
                            point = (
                                alt.Chart(df_current)
                                .mark_circle(size=140, color="#ef4444")
                                .encode(
                                    x=f"{var_choice}:Q",
                                    y="Result:Q",
                                    tooltip=[
                                        alt.Tooltip(
                                            f"{var_choice}:Q",
                                            title=f"Current {var_choice}",
                                            format=",.4f",
                                        ),
                                        alt.Tooltip(
                                            "Result:Q",
                                            title="Current Result",
                                            format=",.4f",
                                        ),
                                    ],
                                )
                            )
                            chart = (line + point).properties(height=360).interactive()
                        else:
                            chart = line.properties(height=360).interactive()

                        st.altair_chart(chart, use_container_width=True)

                        with st.expander("📋 View & Download 1D Data Table"):
                            st.dataframe(df_curve, use_container_width=True)
                    else:
                        st.warning("No valid data points could be plotted across this range.")

            # --- 2D Sensitivity Heatmap & Table ---
            with viz_2d:
                st.caption(
                    "Vary two inputs simultaneously to see how they interact across a grid."
                )
                sel_col1, sel_col2, sel_col3 = st.columns(3)
                with sel_col1:
                    var_x = st.selectbox(
                        "Horizontal Axis (Columns)",
                        options=["a", "b", "c"],
                        index=1,
                        key="var_2d_x",
                    )
                with sel_col2:
                    remaining_vars = [v for v in ["a", "b", "c"] if v != var_x]
                    default_y_idx = 1 if len(remaining_vars) > 1 else 0
                    var_y = st.selectbox(
                        "Vertical Axis (Rows)",
                        options=remaining_vars,
                        index=default_y_idx,
                        key="var_2d_y",
                    )
                with sel_col3:
                    grid_steps = st.slider(
                        "Grid Resolution",
                        min_value=5,
                        max_value=15,
                        value=9,
                        key="slider_2d_grid",
                    )

                fixed_vars = [v for v in ["a", "b", "c"] if v not in (var_x, var_y)]
                fixed_var = fixed_vars[0]
                fixed_val = {"a": a, "b": b, "c": c}[fixed_var]
                st.info(
                    f"Holding **{fixed_var} = {fixed_val:g}** constant while varying **{var_x}** and **{var_y}**."
                )

                val_x = {"a": a, "b": b, "c": c}[var_x]
                val_y = {"a": a, "b": b, "c": c}[var_y]
                def_min_x, def_max_x = get_default_bounds(val_x)
                def_min_y, def_max_y = get_default_bounds(val_y)
                step_x_in = 0.01 if (0 < abs(val_x) < 1) else 1.0
                step_y_in = 0.01 if (0 < abs(val_y) < 1) else 1.0

                gx1, gx2, gy1, gy2 = st.columns(4)
                with gx1:
                    min_x = st.number_input(
                        f"Min '{var_x}'",
                        value=def_min_x,
                        step=step_x_in,
                        format="%.4f",
                        key=f"min_2d_x_{var_x}",
                    )
                with gx2:
                    max_x = st.number_input(
                        f"Max '{var_x}'",
                        value=def_max_x,
                        step=step_x_in,
                        format="%.4f",
                        key=f"max_2d_x_{var_x}",
                    )
                with gy1:
                    min_y = st.number_input(
                        f"Min '{var_y}'",
                        value=def_min_y,
                        step=step_y_in,
                        format="%.4f",
                        key=f"min_2d_y_{var_y}",
                    )
                with gy2:
                    max_y = st.number_input(
                        f"Max '{var_y}'",
                        value=def_max_y,
                        step=step_y_in,
                        format="%.4f",
                        key=f"max_2d_y_{var_y}",
                    )

                if min_x >= max_x or min_y >= max_y:
                    st.warning("Ensure Minimum values are lower than Maximum values for both axes.")
                else:
                    x_vals = [
                        min_x + i * (max_x - min_x) / (grid_steps - 1)
                        for i in range(grid_steps)
                    ]
                    y_vals = [
                        min_y + j * (max_y - min_y) / (grid_steps - 1)
                        for j in range(grid_steps)
                    ]

                    heat_rows = []
                    matrix_data = {}

                    for xv in x_vals:
                        col_label = f"{xv:.4g}"
                        matrix_data[col_label] = {}
                        for yv in y_vals:
                            row_label = f"{yv:.4g}"
                            env = dict(allowed_names)
                            env[var_x] = xv
                            env[var_y] = yv
                            try:
                                res_val = float(eval(expression, {"__builtins__": {}}, env))
                                if math.isfinite(res_val):
                                    heat_rows.append(
                                        {
                                            "x_val": xv,
                                            "y_val": yv,
                                            "x_label": col_label,
                                            "y_label": row_label,
                                            "Result": res_val,
                                            "Result_Text": f"{res_val:,.4g}",
                                        }
                                    )
                                    matrix_data[col_label][row_label] = res_val
                                else:
                                    matrix_data[col_label][row_label] = None
                            except Exception:
                                matrix_data[col_label][row_label] = None

                    if heat_rows:
                        df_heat = pd.DataFrame(heat_rows)
                        midpoint = (df_heat["Result"].min() + df_heat["Result"].max()) / 2.0

                        x_order = [f"{xv:.4g}" for xv in x_vals]
                        y_order = [f"{yv:.4g}" for yv in reversed(y_vals)]

                        base_heat = alt.Chart(df_heat).encode(
                            x=alt.X(
                                "x_label:O",
                                sort=x_order,
                                title=f"Variable {var_x}",
                                axis=alt.Axis(labelAngle=0),
                            ),
                            y=alt.Y(
                                "y_label:O",
                                sort=y_order,
                                title=f"Variable {var_y}",
                            ),
                        )

                        rects = base_heat.mark_rect(cornerRadius=4, stroke="#ffffff", strokeWidth=1).encode(
                            color=alt.Color(
                                "Result:Q",
                                title="Result",
                                scale=alt.Scale(scheme="viridis"),
                            ),
                            tooltip=[
                                alt.Tooltip("x_val:Q", title=f"Variable {var_x}", format=",.4f"),
                                alt.Tooltip("y_val:Q", title=f"Variable {var_y}", format=",.4f"),
                                alt.Tooltip("Result:Q", title="Result", format=",.4f"),
                            ],
                        )

                        if grid_steps <= 10:
                            text_labels = base_heat.mark_text(fontSize=11, fontWeight="bold").encode(
                                text="Result_Text:N",
                                color=alt.condition(
                                    alt.datum.Result > midpoint,
                                    alt.value("#1e1b4b"),
                                    alt.value("#ffffff"),
                                ),
                            )
                            heat_chart = (rects + text_labels).properties(height=420)
                        else:
                            heat_chart = rects.properties(height=420)

                        st.altair_chart(heat_chart, use_container_width=True)

                        df_matrix = pd.DataFrame(matrix_data)
                        df_matrix.index.name = f"{var_y} \\ {var_x}"

                        with st.expander("🔢 View & Export 2D Sensitivity Matrix Table", expanded=True):
                            st.dataframe(
                                df_matrix.style.format("{:,.4g}", na_rep="—"),
                                use_container_width=True,
                            )
                            csv_bytes = df_matrix.to_csv().encode("utf-8")
                            st.download_button(
                                label="📥 Download 2D Matrix as CSV (Excel)",
                                data=csv_bytes,
                                file_name=f"sensitivity_{var_y}_vs_{var_x}.csv",
                                mime="text/csv",
                                key="dl_2d_matrix",
                            )
                    else:
                        st.warning("Could not compute valid numbers for this 2D grid range.")

        except Exception as e:
            st.error(f"Could not evaluate formula: {e}")

# --- Goal Seek Solver Tab ---
with tab_goalseek:
    st.subheader("🎯 Goal Seek Solver")
    st.caption(
        "Specify a target output and select which variable to solve for. The calculator will automatically find the exact input value required."
    )

    gs_a = st.session_state.val_a
    gs_b = st.session_state.val_b
    gs_c = st.session_state.val_c

    # Current formula evaluation for reference
    allowed_names_gs = {
        "a": gs_a,
        "b": gs_b,
        "c": gs_c,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
    }

    try:
        current_eval_res = float(eval(expression, {"__builtins__": {}}, allowed_names_gs))
    except Exception:
        current_eval_res = 100.0

    target_val = st.number_input(
        "Target Output Result",
        value=float(round(current_eval_res * 1.2, 2)),
        step=10.0,
        format="%.4f",
        help="The desired final result you want your formula to equal.",
    )

    solve_var = st.selectbox(
        "Variable to Solve For",
        options=["a", "b", "c"],
        index=2,
        help="Choose which variable (a, b, or c) the solver should adjust.",
    )

    current_solve_val = {"a": gs_a, "b": gs_b, "c": gs_c}[solve_var]
    bnd_min, bnd_max = get_default_bounds(current_solve_val)
    if bnd_min == bnd_max:
        bnd_min, bnd_max = -100.0, 100.0

    sc1, sc2 = st.columns(2)
    with sc1:
        search_min = st.number_input(
            f"Search Minimum Boundary for '{solve_var}'",
            value=float(bnd_min - abs(bnd_min) * 0.5 - 10),
            step=1.0,
            format="%.4f",
            key="gs_min",
        )
    with sc2:
        search_max = st.number_input(
            f"Search Maximum Boundary for '{solve_var}'",
            value=float(bnd_max + abs(bnd_max) * 0.5 + 10),
            step=1.0,
            format="%.4f",
            key="gs_max",
        )

    if st.button("🚀 Run Goal Seek", type="primary", use_container_width=True):
        def objective(val_to_test):
            env = dict(allowed_names_gs)
            env[solve_var] = val_to_test
            return float(eval(expression, {"__builtins__": {}}, env))

        solved_val, err_reason = goal_seek(objective, target_val, search_min, search_max)

        if err_reason:
            st.error(f"Goal Seek could not find a solution: {err_reason}")
        elif solved_val is not None:
            # Verify solved result
            check_env = dict(allowed_names_gs)
            check_env[solve_var] = solved_val
            final_check = float(eval(expression, {"__builtins__": {}}, check_env))

            st.success("🎯 Goal Seek Successful!")
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="result-label">Required Solved Value for {solve_var}</div>
                    <div class="result-value">{solved_val:,.6g}</div>
                    <div class="result-formula">Achieves target output: {final_check:,.6g} (Formula: {expression})</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Button to apply solved value back to session state
            if st.button(f"📥 Apply Solved Value ({solve_var} = {solved_val:,.4g}) to Calculator"):
                if solve_var == "a":
                    st.session_state.val_a = solved_val
                elif solve_var == "b":
                    st.session_state.val_b = solved_val
                elif solve_var == "c":
                    st.session_state.val_c = solved_val
                st.session_state.history.insert(
                    0, f"Goal Seek: Target {target_val:g} solved {solve_var} = {solved_val:,.4g}"
                )
                st.rerun()

# 5. Calculation History Section
if st.session_state.history:
    st.divider()
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.subheader("🕓 Saved Calculations")
    with col_h2:
        if st.button("Clear"):
            st.session_state.history = []
            st.rerun()
    for item in st.session_state.history:
        st.code(item, language=None)
