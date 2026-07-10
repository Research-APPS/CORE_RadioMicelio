class OntologizarRouter:
    # corpus_app se añade aquí (no solo ontologizar_app/airam_app) porque tiene
    # ForeignKey reales hacia ontologizar_app.Concept (Mencion.concept,
    # RelacionSugerida.*_entidad) — sin estar en el mismo grupo de enrutamiento,
    # allow_relation() bloquearía esas FKs entre bases de datos distintas.
    route_app_labels = {"ontologizar_app", "airam_app", "corpus_app"}
    db_alias = "ontologizar_db"

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.db_alias
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.db_alias
        return None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if labels & self.route_app_labels:
            return labels <= self.route_app_labels
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.db_alias
        if db == self.db_alias:
            return False
        return None
