import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class ExpenseSearchFilterBar extends StatefulWidget {
  final String searchQuery;
  final Function(String) onSearchChanged;
  final String? categoryFilter;
  final List<String> categoryOptions;
  final Function(String?) onCategoryFilterChanged;
  final String? approvalStatusFilter;
  final List<String> approvalStatusOptions;
  final Function(String?) onApprovalStatusFilterChanged;
  final Function(DateTime?, DateTime?) onDateRangeChanged;

  const ExpenseSearchFilterBar({
    super.key,
    required this.searchQuery,
    required this.onSearchChanged,
    this.categoryFilter,
    required this.categoryOptions,
    required this.onCategoryFilterChanged,
    this.approvalStatusFilter,
    required this.approvalStatusOptions,
    required this.onApprovalStatusFilterChanged,
    required this.onDateRangeChanged,
  });

  @override
  State<ExpenseSearchFilterBar> createState() => _ExpenseSearchFilterBarState();
}

class _ExpenseSearchFilterBarState extends State<ExpenseSearchFilterBar> {
  late TextEditingController _searchController;
  DateTime? _startDate;
  DateTime? _endDate;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController(text: widget.searchQuery);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _selectDateRange() async {
    final DateTimeRange? picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
      initialDateRange: _startDate != null && _endDate != null
          ? DateTimeRange(start: _startDate!, end: _endDate!)
          : null,
    );

    if (picked != null) {
      setState(() {
        _startDate = picked.start;
        _endDate = picked.end;
      });
      widget.onDateRangeChanged(_startDate, _endDate);
    }
  }

  void _clearDateFilter() {
    setState(() {
      _startDate = null;
      _endDate = null;
    });
    widget.onDateRangeChanged(null, null);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.2),
            spreadRadius: 1,
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          // 基本検索バー
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: '説明、プロジェクト名、カテゴリで検索...',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                              widget.onSearchChanged('');
                            },
                          )
                        : null,
                    border: const OutlineInputBorder(),
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                  onChanged: widget.onSearchChanged,
                ),
              ),
              const SizedBox(width: 8),
              
              // フィルター展開ボタン
              IconButton(
                icon: Icon(
                  _isExpanded ? Icons.filter_list_off : Icons.filter_list,
                  color: _isExpanded ? Colors.green : null,
                ),
                onPressed: () {
                  setState(() {
                    _isExpanded = !_isExpanded;
                  });
                },
                tooltip: 'フィルター',
              ),
            ],
          ),
          
          // 展開可能なフィルター部分
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            height: _isExpanded ? null : 0,
            child: _isExpanded
                ? Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: Column(
                      children: [
                        // カテゴリフィルター
                        Row(
                          children: [
                            const SizedBox(
                              width: 80,
                              child: Text(
                                'カテゴリ:',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                            ),
                            Expanded(
                              child: DropdownButtonFormField<String>(
                                value: widget.categoryFilter,
                                decoration: const InputDecoration(
                                  border: OutlineInputBorder(),
                                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  isDense: true,
                                ),
                                items: widget.categoryOptions.map((category) => DropdownMenuItem(
                                  value: category == '全て' ? null : category,
                                  child: Text(category),
                                )).toList(),
                                onChanged: widget.onCategoryFilterChanged,
                                hint: const Text('全て'),
                              ),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 12),
                        
                        // 承認状況フィルター
                        Row(
                          children: [
                            const SizedBox(
                              width: 80,
                              child: Text(
                                '承認状況:',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                            ),
                            Expanded(
                              child: DropdownButtonFormField<String>(
                                value: widget.approvalStatusFilter,
                                decoration: const InputDecoration(
                                  border: OutlineInputBorder(),
                                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  isDense: true,
                                ),
                                items: widget.approvalStatusOptions.map((status) => DropdownMenuItem(
                                  value: status == '全て' ? null : status,
                                  child: Text(status),
                                )).toList(),
                                onChanged: widget.onApprovalStatusFilterChanged,
                                hint: const Text('全て'),
                              ),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 12),
                        
                        // 日付範囲フィルター
                        Row(
                          children: [
                            const SizedBox(
                              width: 80,
                              child: Text(
                                '期間:',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                            ),
                            Expanded(
                              child: InkWell(
                                onTap: _selectDateRange,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                                  decoration: BoxDecoration(
                                    border: Border.all(color: Colors.grey),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Row(
                                    children: [
                                      const Icon(Icons.date_range, size: 20),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          _startDate != null && _endDate != null
                                              ? '${DateFormat('yyyy/MM/dd').format(_startDate!)} - ${DateFormat('yyyy/MM/dd').format(_endDate!)}'
                                              : '期間を選択',
                                          style: TextStyle(
                                            color: _startDate != null ? Colors.black : Colors.grey,
                                          ),
                                        ),
                                      ),
                                      if (_startDate != null)
                                        IconButton(
                                          icon: const Icon(Icons.clear, size: 18),
                                          onPressed: _clearDateFilter,
                                          constraints: const BoxConstraints(),
                                          padding: EdgeInsets.zero,
                                        ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 12),
                        
                        // フィルタークリアボタン
                        Row(
                          children: [
                            const Spacer(),
                            TextButton.icon(
                              onPressed: () {
                                _searchController.clear();
                                widget.onSearchChanged('');
                                widget.onCategoryFilterChanged(null);
                                widget.onApprovalStatusFilterChanged(null);
                                _clearDateFilter();
                              },
                              icon: const Icon(Icons.clear_all),
                              label: const Text('すべてクリア'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  )
                : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}