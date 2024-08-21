def current_path(request):
    '''Adds the name of the view as context to all templates'''
    return {'current_path': request.path, 'current_view': request.resolver_match.view_name if request.resolver_match else ''}
