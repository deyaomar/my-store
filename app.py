# --- 4. التقارير والإحصائيات المتقدمة (تعديل الخيار ب) ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي للأداء</h1>", unsafe_allow_html=True)
        
        # إضافة فلتر التاريخ في الأعلى
        st.markdown("### 📅 اختر الفترة المراد تحليلها")
        c_date1, c_date2 = st.columns(2)
        with c_date1:
            start_date = st.date_input("من تاريخ", datetime.now().date())
        with c_date2:
            end_date = st.date_input("إلى تاريخ", datetime.now().date())

        # تحويل أعمدة التاريخ لضمان دقة المقارنة
        st.session_state.sales_df['date_only'] = pd.to_datetime(st.session_state.sales_df['date']).dt.date
        st.session_state.expenses_df['date_only'] = pd.to_datetime(st.session_state.expenses_df['date']).dt.date
        st.session_state.waste_df['date_only'] = pd.to_datetime(st.session_state.waste_df['date']).dt.date

        # فلترة البيانات بناءً على التاريخ المختار
        mask_sales = (st.session_state.sales_df['date_only'] >= start_date) & (st.session_state.sales_df['date_only'] <= end_date)
        mask_exp = (st.session_state.expenses_df['date_only'] >= start_date) & (st.session_state.expenses_df['date_only'] <= end_date)
        mask_waste = (st.session_state.waste_df['date_only'] >= start_date) & (st.session_state.waste_df['date_only'] <= end_date)

        f_sales = st.session_state.sales_df[mask_sales]
        f_exp = st.session_state.expenses_df[mask_exp]
        f_waste = st.session_state.waste_df[mask_waste]

        # حساب الحسابات للفترة المختارة فقط
        total_sales = f_sales['amount'].sum()
        total_profit_raw = f_sales['profit'].sum() # الربح من البيع فقط
        total_exp = f_exp['amount'].sum()
        total_waste = f_waste['loss_value'].sum()
        net_profit = total_profit_raw - total_exp - total_waste

        # عرض الكروت المالية
        st.write(f"#### 📜 ملخص الفترة من {start_date} إلى {end_date}")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h3>💰 مبيعات الفترة</h3><h2>{total_sales:,.1f} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h3>💸 مصروفات</h3><h2>{total_exp:,.1f} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h3>🍎 تالف</h3><h2>{total_waste:,.1f} ₪</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='report-card' style='border-right-color:#27ae60;'><h3>✅ صافي الربح</h3><h2>{net_profit:,.1f} ₪</h2></div>", unsafe_allow_html=True)

        # إحصائيات إضافية للفترة
        st.write("---")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("🔝 الأكثر مبيعاً (كمية)")
            if not f_sales.empty:
                top_qty = f_sales.groupby('item')['amount'].count().reset_index() # عدد مرات البيع
                fig_qty = px.pie(top_qty, values='amount', names='item', hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
                st.plotly_chart(fig_qty, use_container_width=True)
            else: st.info("لا توجد مبيعات في هذه الفترة")

        with col_chart2:
            st.subheader("💵 طرق الدفع")
            if not f_sales.empty:
                method_counts = f_sales.groupby('method')['amount'].sum().reset_index()
                fig_method = px.bar(method_counts, x='method', y='amount', color='method', color_discrete_map={'نقداً': '#27ae60', 'تطبيق': '#2980b9'})
                st.plotly_chart(fig_method, use_container_width=True)
