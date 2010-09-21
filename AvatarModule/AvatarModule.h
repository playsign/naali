// For conditions of distribution and use, see copyright notice in license.txt

#ifndef incl_AvatarModule_h
#define incl_AvatarModule_h

#include "IModule.h"
#include "ModuleLoggingFunctions.h"
#include "AvatarModuleApi.h"
#include "InputServiceInterface.h"
#include "SceneManager.h"

#include "WorldStream.h"

#include <QObject>
#include <QList>
#include <QMap>

namespace AvatarModule
{
    class Avatar;
    class AvatarControllable;
    class AvatarEditor;

    typedef boost::shared_ptr<Avatar> AvatarPtr;
    typedef boost::shared_ptr<AvatarControllable> AvatarControllablePtr;
    typedef boost::shared_ptr<AvatarEditor> AvatarEditorPtr;

    typedef QMap<RexUUID, entity_id_t> UUID_map;
            
    class AV_MODULE_API AvatarModule : public QObject, public IModule
    {

    Q_OBJECT
    
    static const std::string &NameStatic();

    public:
        AvatarModule();
        virtual ~AvatarModule();

		void Load();
        void Initialize();
        void PostInitialize();
        void Update(f64 frametime);
        bool HandleEvent(event_category_id_t category_id, event_id_t event_id, IEventData* data);

        MODULE_LOGGING_FUNCTIONS
    
    private slots:
        //! Populate service_category_identifiers_
        void SubscribeToEventCategories();

    public slots:
        Scene::EntityPtr GetAvatarEntity(const RexUUID &uuid);
        Scene::EntityPtr GetAvatarEntity(entity_id_t entity_id);

        ProtocolUtilities::WorldStreamPtr GetServerConnection() { return world_stream_; }

        AvatarPtr GetAvatarHandler() { return avatar_handler_; }
        AvatarEditorPtr GetAvatarEditor() { return avatar_editor_; }
        AvatarControllablePtr GetAvatarControllable() { return avatar_controllable_; }

        void RegisterFullId(const RexUUID &full_uuid, entity_id_t entity_id);
        void UnregisterFullId(const RexUUID &full_uuid);

    private:
        //! Current query categories
        QStringList event_query_categories_;

        //! Current subscribed category events
        QMap<QString, event_category_id_t> service_category_identifiers_;

        //! AvatarModules input context
        InputContextPtr input_context_;

        AvatarPtr avatar_handler_;
        AvatarControllablePtr avatar_controllable_;
        AvatarEditorPtr avatar_editor_;

        ProtocolUtilities::WorldStreamPtr world_stream_;

        UUID_map uuid_to_local_id_;
    };
}
#endif