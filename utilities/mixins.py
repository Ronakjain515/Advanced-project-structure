from django.db import models
from django.utils import timezone


class CustomModelMixin(models.Model):
    """
    Mixin class for creating util details.
    """

    is_deleted = models.BooleanField(null=False, blank=False, default=False)
    created_by = models.ForeignKey("users.CustomUser", null=False, blank=False, on_delete=models.CASCADE, related_name="created_by_%(class)s")
    updated_by = models.ForeignKey("users.CustomUser", null=False, blank=False, on_delete=models.CASCADE, related_name="updated_by_%(class)s")
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)

    class Meta:
        abstract = True


class DynamicFieldsSerializerMixin(object):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DynamicFieldsViewMixin(object):
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()

        fields = None
        if self.request.method == "GET":
            query_fields = self.request.query_params.get("fields", None)

            if query_fields:
                fields = tuple(query_fields.split(","))

        kwargs["context"] = self.get_serializer_context()
        kwargs["fields"] = fields

        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """
        Method to get the context for serializer.
        """
        fields = self.request.GET.get("fields")
        if fields:
            fields_list = fields.split(",")
            context_dict = {}
            for field in fields_list:
                if "__" in field:
                    field_list = field.split("__")
                    if field_list[0] in context_dict:
                        context_dict[field_list[0]].append(field_list[1])
                    else:
                        context_dict[field_list[0]] = [field_list[1]]
            return context_dict
        return {}
