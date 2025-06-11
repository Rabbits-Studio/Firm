from django.shortcuts import render, get_object_or_404, redirect
from .models import Issue
from .forms import IssueForm

# List all issues
def issue_list(request):
    issues = Issue.objects.all()
    return render(request, 'core/issue_list.html', {'issues': issues})

# Detail view of one issue
def issue_detail(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    return render(request, 'core/issue_detail.html', {'issue': issue})

# Create new issue
def issue_create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)

            # Set the converted AD dates manually
            issue.issue_date = form.cleaned_data['issue_date']
            issue.final_date = form.cleaned_data['final_date']
            issue.total_days = form.cleaned_data['total_days']

            # You can add auto-calculated logic for interest/total amount here too
            issue.save()
            return redirect('issue_list')
    else:
        form = IssueForm()
    return render(request, 'core/issue_form.html', {'form': form})


# Update existing issue
def issue_update(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            return redirect('issue_detail', pk=issue.pk)
    else:
        form = IssueForm(instance=issue)
    return render(request, 'core/issue_form.html', {'form': form})

# Delete issue
def issue_delete(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.method == 'POST':
        issue.delete()
        return redirect('issue_list')
    return render(request, 'core/issue_confirm_delete.html', {'issue': issue})
